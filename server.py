import os
import json
import base64
from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai

app = Flask(__name__)
CORS(app)  # للسماح بالتواصل من تطبيق الموبايل / Flutter

# ضبط مفتاح API الخاص بـ Gemini من بيئة التشغيل
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "ضع_مفتاحك_هنا_إن_لم_تستخدم_المتغيرات")
genai.configure(api_key=GEMINI_API_KEY)

# استخدام نموذج Gemini Vision
model = genai.GenerativeModel('gemini-1.5-flash')

@app.route('/', methods=['GET'])
def health_check():
    return jsonify({
        "status": "online",
        "service": "Saya Diet AI Vision Backend",
        "version": "1.0.0"
    }), 200

@app.route('/api/v1/analyze-meal', methods=['POST'])
def analyze_meal():
    try:
        data = request.get_json()
        
        if not data or 'image_base64' not in data:
            return jsonify({"error": "يرجى إرسال الصورة بصيغة image_base64"}), 400
            
        user_goal = data.get("user_goal", "إنقاص الوزن")  # "زيادة وزن"، "إنقاص وزن"، "ثبات"
        target_calories = data.get("target_calories", 2000)

        # فك تشفير الصورة
        image_bytes = base64.b64decode(data['image_base64'])

        prompt = f"""
        قم بتحليل صورة الطعام التالية بدقة بالغة باللغة العربية لتطبيق (صايا دايت).
        إذا كانت الصورة تحتوي على عنصر واحد (مثل موزة أو تفاحة)، حدد الحجم واللون والنضج.
        إذا كانت وجبة مكتملة (مثل كبسة، سلطة، ستيك)، قم بتفكيك المكونات وحساب حجم كل صنف.

        هدف المستخدم: {user_goal}
        السعرات اليومية المستهدفة: {target_calories}

        أرجع النتيجة حصراً بصيغة JSON بالهيكل التالي بدون أي مقدمات أو شروحات خارج الـ JSON:
        {{
          "itemName": "اسم الوجبة أو العنصر الرئيسي",
          "estimatedWeightGrams": 150,
          "calories": 210,
          "proteinGrams": 5.0,
          "carbsGrams": 30.0,
          "fatGrams": 2.5,
          "fiberGrams": 3.0,
          "vitamins": ["فيتامين C", "بوتاسيوم"],
          "ingredients": [
            {{"name": "مكون 1", "portion": "حبة متوسطة", "calories": 100}}
          ],
          "advice": "نصيحة غذائية مخصصة بناءً على هدف المستخدم",
          "portionStatus": "مناسبة"
        }}
        """

        response = model.generate_content([
            prompt,
            {'mime_type': 'image/jpeg', 'data': image_bytes}
        ])

        # تنظيف وتنسيق نص الاستجابة لاستخراج الـ JSON
        raw_text = response.text.replace('```json', '').replace('```', '').strip()
        result_json = json.loads(raw_text)

        return jsonify({
            "success": True,
            "data": result_json
        }), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

if __name__ == '__main__':
    # تشغيل الخادم على المنفذ 5000
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)