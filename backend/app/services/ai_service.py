import os
import google.generativeai as genai
import logging

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

model = None
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        logger.info("Gemini API initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize Gemini API: {e}")

def get_action_suggestion(anomaly_info: dict) -> str:
    """
    Returns an AI-generated or rule-based fallback action suggestion 
    for an anomalous machine state.
    """
    if model is None:
        return _fallback_suggestion(anomaly_info)
    
    try:
        prompt = f"""
        Sen tekstil fabrikasındaki yöneticilere tavsiye veren bir yapay zeka asistanısın.
        Aşağıdaki makinede anomali tespit edildi. Lütfen çok kısa (1-2 cümle) ve net aksiyon odaklı bir teknik öneri sun:
        Veriler:
        - Tesis (Facility): {anomaly_info.get('facility_type', 'Bilinmiyor')}
        - Makine Hızı: {anomaly_info.get('machine_speed', 'Bilinmiyor')}
        - Hata Oranı: %{anomaly_info.get('defect_rate', 'Bilinmiyor')}
        - Kalite Skoru: {anomaly_info.get('quality_score', 'Bilinmiyor')}
        - Enerji İsrafı Bayrağı: {'Evet' if anomaly_info.get('energy_waste_flag') == 1 else 'Hayır'}
        """
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        logger.error(f"Gemini API execution error: {e}")
        return _fallback_suggestion(anomaly_info)

def _fallback_suggestion(anomaly_info: dict) -> str:
    # Rule-based fallback mechanism as requested by user
    defect_rate = float(anomaly_info.get('defect_rate', 0.0))
    energy_waste = int(anomaly_info.get('energy_waste_flag', 0))
    
    if defect_rate > 2.0 and energy_waste == 1:
        return "KRİTİK: Makinede hem kalite düşüşü hem de enerji kaybı var. Termal kaçak veya mekanik sıkışma olabilir, acil bakım planlayın."
    elif defect_rate > 2.0:
        return "UYARI: Hata oranı eşiğin üzerinde. Hızı düşürüp gerginlik ayarlarını kontrol edin."
    elif energy_waste == 1:
        return "DİKKAT: Üretim normal ancak enerji tüketimi gereksiz yüksek. Isı kaybı veya motor zorlanması olabilir."
    else:
        return "Anomali şüphesi. Operatörün makine titreşimlerini ve sıcaklıklarını gözle kontrol etmesi önerilir."
