from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
import logging

# 初始化 Flask 应用
app = Flask(__name__)
CORS(app)  # 启用 CORS 支持

# 连接 MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['drone_questions']
collection = db['questions']

# 配置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@app.route('/questions', methods=['GET'])
def get_questions():
    """
    获取所有题目
    """
    try:
        # 从 MongoDB 查询所有题目，并排除 _id 字段
        questions = list(collection.find({}, {'_id': 0}))
        logger.debug(f"Fetched questions: {questions}")  # 打印查询结果
        return jsonify(questions)
    except Exception as e:
        logger.error(f"Error fetching questions: {e}")
        return jsonify({'error': '服务器内部错误'}), 500

@app.route('/questions/<int:question_id>/keywords', methods=['POST'])
def update_keywords(question_id):
    """
    更新题目的关键词
    """
    try:
        data = request.json
        logger.debug(f"Received data for question {question_id}: {data}")  # 打印请求数据

        if not data:
            logger.warning(f"Invalid data received for question {question_id}")
            return jsonify({'error': '请求数据无效'}), 400

        # 查询题目是否存在
        question_doc = collection.find_one(
            {'questions.question_id': question_id},
            {'questions.$': 1}  # 只返回匹配的题目
        )

        if not question_doc or 'questions' not in question_doc or len(question_doc['questions']) == 0:
            logger.warning(f"Question {question_id} not found")
            return jsonify({'error': '未找到题目'}), 404

        # 获取匹配的题目
        question = question_doc['questions'][0]

        # 更新关键词
        if 'keywords' not in question:
            question['keywords'] = []
        question['keywords'] = data

        # 更新 MongoDB
        result = collection.update_one(
            {'questions.question_id': question_id},
            {'$set': {'questions.$.keywords': data}}
        )
        logger.debug(f"Update result for question {question_id}: {result.raw_result}")  # 打印更新结果

        if result.matched_count == 0:  # 检查是否找到题目
            logger.warning(f"Question {question_id} not found")
            return jsonify({'error': '未找到题目'}), 404

        if result.modified_count == 0:  # 检查是否更新成功
            logger.info(f"No changes made for question {question_id}")
            return jsonify({'status': 'success', 'message': '数据未更改'}), 200

        logger.info(f"Keywords updated successfully for question {question_id}")
        return jsonify({'status': 'success'})
    except Exception as e:
        logger.error(f"Error updating keywords for question {question_id}: {e}")
        return jsonify({'error': '服务器内部错误'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)