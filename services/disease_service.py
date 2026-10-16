import os
from config import Config
from ai.disease_detection import DiseaseDetector

detector = DiseaseDetector(Config.DISEASE_MODEL_PATH)

class DiseaseService:
    @staticmethod
    def process_and_diagnose(image_path, demo_mode=False):
        return detector.scan_crop(image_path, demo_mode=demo_mode)
        
    @staticmethod
    def is_model_configured():
        return detector.model_loaded
