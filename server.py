import os
import json
import base64
from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai

app = Flask(__name__)
CORS(app)

# ضبط مفتاح Gemini API من متغيرات البيئة في Render
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
genai.configure(api_key=GEMINI_API_KEY)

# استخدام نموذج Gemini 1.5 Flash للسرعة ودقة تحليل الصور
model = genai.GenerativeModel('gemini-1.5-flash')

# 1. دعم مسار الفحص الأساسي والجذري لتجنب أخطاء 404
@app.route('/', methods=['GET'])
def health_check_root():
    return jsonify({
        "status": "ok",
        "service": "Saya Diet AI Vision Backend",
        "version": "2.0.0"
    }), 200

@app.route('/healthz', methods=['GET'])
def health_check_path():
    return jsonify({
        "status": "ok",
        "version": "2.0.0"
    }), 200

# 2. مسار التحليل المتوافق مع الـ APK
@app.route('/api/v1/analyze-meal', methods=['POST'])
def analyze_meal():
    try:
        # التحقق الاختياري من رمز الوصول (Token) إذا أرسله الـ APK في الهيدر لكي لا يرجع 401
        auth_header = request.headers.get('Authorization')
        # (يمكنك إضافة التحقق الفعلي هنا إن رغبت، أو السماح بالمرور لتسهيل الاختبار)

        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "البيانات المرسلة فارغة"}), 400
            
        # دعم استقبال الصورة بأكثر من مفتاح يرسله التطبيق
        img_data = data.get('image') or data.get('image_base64')
        if not img_data:
            return jsonify({"success": False, "error": "يرجى إرسال الصورة بالحقل image أو image_base64"}), 400

        user_goal = data.get("user_goal", "إنقاص الوزن")
        target_calories = data.get("target_calories", 1800)

        # تنظيف بيانات الـ base64 إذا كان مضافاً إليها رأس البيانات
        if ',' in img_data:
            img_data = img_data.split(',')[1]

        image_bytes = base64.b64decode(img_data)

        prompt = f"""
        قم بتحليل صورة الوجبة أو الأطعمة التالية بدقة بالغة لتطبيق التغذية (صايا دايت).
        هدف المستخدم: {user_goal}
        السعرات المستهدفة: {target_calories}

        قم بتفكيك عناصر الوجبة الظاهرة في الصورة إلى قائمة أصناف دقيقة.
        أرجع النتيجة حصراً بصيغة JSON صحيحة ومتوافقة تماماً مع الهيكل التالي دون أي نصوص أو شروحات إضافية خارجه:
        {{
          "success": true,
          "message": "تم تحليل الوجبة بنجاح",
          "total_calories": 450,
          "total_protein": 25.5,
          "total_carbs": 45.0,
          "total_fat": 12.0,
          "total_fiber": 6.0,
          "items": [
            {{
              "item_name": "اسم الصنف الأول بالعربي",
              "portion": "حبة متوسطة أو كوب",
              "weight_grams": 150,
              "calories": 250,
              "protein_grams": 15.0,
              "carbs_grams": 30.0,
              "fat_grams": 5.0,
              "fiber_grams": 4.0
            }}
          ],
          "advice": "نصيحة غذائية قصيرة ومفيدة تناسب هدف المستخدم"
        }}
        """

        response = model.generate_content([
            prompt,
            {'mime_type': 'image/jpeg', 'data': image_bytes}
        ])

        raw_text = response.text.replace('```json', '').replace('```', '').strip()
        result_json = json.loads(raw_text)

        return jsonify(result_json), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
