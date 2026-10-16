from ai.crop_recommendation import recommend_crops

class RecommendationService:
    @staticmethod
    def get_crop_recommendations(location, land_size_acres, soil_type, season, water_availability):
        return recommend_crops(location, land_size_acres, soil_type, season, water_availability)
