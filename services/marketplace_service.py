"""
Marketplace Service for AgriTrust
Coordinates product listings, search/filters, secure transactional orders,
harvest reservations, and waste reduction analytics.
"""

import math
from extensions import db
from models.product import Product
from models.order import Order
from models.reservation import FutureHarvest, Reservation
from models.harvest import HarvestBatch
from datetime import datetime, date, timedelta

class MarketplaceService:
    @staticmethod
    def search_products(query=None, category=None, location=None, max_price=None):
        q = Product.query.filter(Product.availability_status == 'Available', Product.quantity > 0)
        
        if query:
            search_str = f"%{query}%"
            q = q.filter(Product.title.ilike(search_str) | Product.description.ilike(search_str))
        if category and category != 'All':
            q = q.filter(Product.category == category)
        if location:
            q = q.filter(Product.location.ilike(f"%{location}%"))
        if max_price:
            try:
                p = float(max_price)
                q = q.filter(Product.price_per_unit <= p)
            except ValueError:
                pass

        return q.order_by(Product.created_at.desc()).all()

    @staticmethod
    def place_order(buyer_id, product_id, quantity, delivery_address, contact_phone, notes=""):
        """
        Places order with atomic stock decrement and transaction protection.
        """
        try:
            qty = float(quantity)
            if qty <= 0:
                return False, "Order quantity must be greater than zero.", None

            product = Product.query.filter_by(id=product_id).with_for_update().first()
            if not product:
                return False, "Product listing not found.", None

            # Enforce Quality Verification requirement before sale
            if product.batch and product.batch.verification_stage != 'Quality Verified':
                return False, f"Cannot place order: Produce batch #{product.batch.batch_code} is currently '{product.batch.verification_stage}' and requires official admin Quality Verification before direct purchase orders can be placed.", None

            if product.quantity < qty:
                return False, f"Requested quantity ({qty} {product.unit}) exceeds available stock ({product.quantity} {product.unit}).", None

            # Calculate total
            total = round(qty * product.price_per_unit, 2)
            
            # Decrement product stock
            product.quantity = round(product.quantity - qty, 2)
            if product.quantity <= 0:
                product.availability_status = 'Sold Out'

            # Create Order
            order = Order(
                buyer_id=buyer_id,
                product_id=product.id,
                quantity=qty,
                unit_price=product.price_per_unit,
                total_amount=total,
                status='Pending Payment',
                payment_status='Pending Payment (Pay on Delivery / Demo)',
                delivery_address=delivery_address,
                contact_phone=contact_phone,
                notes=notes
            )
            db.session.add(order)
            db.session.commit()
            return True, "Order successfully placed! Direct notification sent to the farmer.", order
        except Exception as e:
            db.session.rollback()
            return False, f"Failed to place order due to database error: {str(e)}", None

    @staticmethod
    def reserve_future_harvest(buyer_id, future_harvest_id, reserved_qty, phone, address, notes=""):
        """
        Safely reserves quantities on upcoming future harvests.
        """
        try:
            req_qty = float(reserved_qty)
            if math.isnan(req_qty) or math.isinf(req_qty) or req_qty <= 0:
                return False, "Reservation quantity must be a valid positive number.", None

            harvest = FutureHarvest.query.filter_by(id=future_harvest_id).with_for_update().first()
            if not harvest:
                return False, "Future harvest listing not found.", None

            remaining = harvest.remaining_quantity
            if req_qty > remaining:
                return False, f"Reservation quantity ({req_qty} kg) exceeds remaining available harvest ({remaining} kg).", None

            harvest.reserved_quantity = round(harvest.reserved_quantity + req_qty, 2)
            if harvest.remaining_quantity <= 0:
                harvest.status = 'Fully Reserved'
            else:
                harvest.status = 'Partially Reserved'

            total_est = round(req_qty * harvest.target_price_per_kg, 2)

            res = Reservation(
                user_id=buyer_id,
                future_harvest_id=harvest.id,
                farmer_id=harvest.farmer_id,
                crop_name=harvest.crop_name,
                reserved_quantity=req_qty,
                unit_price=harvest.target_price_per_kg,
                total_estimated_amount=total_est,
                expected_harvest_date=harvest.expected_harvest_date,
                status='Confirmed',
                contact_phone=phone,
                delivery_address=address,
                notes=notes
            )
            db.session.add(res)
            db.session.commit()
            return True, "Harvest reservation confirmed! Farmer notified for post-harvest priority dispatch.", res
        except Exception as e:
            db.session.rollback()
            return False, f"Failed to complete reservation: {str(e)}", None

    @staticmethod
    def cancel_reservation(reservation_id, user_id, user_role):
        """
        LOG-02: Safely cancels a harvest reservation and restores reserved quantity exactly once.
        """
        try:
            res = Reservation.query.filter_by(id=reservation_id).with_for_update().first()
            if not res:
                return False, "Reservation not found."

            # Authorization: Only booking buyer, owning farmer, or admin can cancel
            if res.user_id != user_id and res.farmer_id != user_id and user_role != 'ADMIN':
                return False, "Unauthorized: Only the booking buyer or owning farmer can cancel this reservation."

            if res.status == 'Cancelled':
                return False, "Reservation has already been cancelled."

            harvest = FutureHarvest.query.filter_by(id=res.future_harvest_id).with_for_update().first()
            if harvest:
                harvest.reserved_quantity = max(0.0, round(harvest.reserved_quantity - res.reserved_quantity, 2))
                if harvest.remaining_quantity > 0:
                    if harvest.reserved_quantity > 0:
                        harvest.status = 'Partially Reserved'
                    else:
                        harvest.status = 'Open for Reservation'

            res.status = 'Cancelled'
            db.session.commit()
            return True, f"Reservation for '{res.crop_name}' ({res.reserved_quantity} kg) cancelled and harvest quota restored."
        except Exception as e:
            db.session.rollback()
            return False, f"Failed to cancel reservation: {str(e)}"

    @staticmethod
    def get_waste_reduction_insights(farmer_id):
        """
        Computes unsold produce risks and suggests interventions.
        """
        today = date.today()
        # Find active products for this farmer with unsold quantities
        unsold_products = Product.query.filter(
            Product.user_id == farmer_id,
            Product.quantity > 0,
            Product.availability_status == 'Available'
        ).all()

        high_risk_items = []
        moderate_risk_items = []

        for p in unsold_products:
            days_since_harvest = (today - p.harvest_date).days
            if days_since_harvest > 5 and p.category == 'Vegetables':
                high_risk_items.append({
                    'product': p,
                    'days_since_harvest': days_since_harvest,
                    'risk_level': 'High Spoilage Risk',
                    'action': 'Offer 15-20% Quick-Sale Discount to institutional buyers'
                })
            elif days_since_harvest > 2:
                moderate_risk_items.append({
                    'product': p,
                    'days_since_harvest': days_since_harvest,
                    'risk_level': 'Moderate Shelf-Life Risk',
                    'action': 'Highlight on Community Demand Board'
                })

        return {
            'unsold_count': len(unsold_products),
            'total_unsold_kg': sum(p.quantity for p in unsold_products),
            'high_risk_items': high_risk_items,
            'moderate_risk_items': moderate_risk_items
        }
