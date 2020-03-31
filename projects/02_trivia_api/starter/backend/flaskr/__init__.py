import os
from flask import Flask, request, abort, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from flask_cors import CORS
import random
import logging

from models import db, setup_db, Question, Category

logging.basicConfig(level=logging.DEBUG)

QUESTIONS_PER_PAGE = 10

def paginate_questions(request, selection):
  page = request.args.get('page', 1, type=int)
  start =  (page - 1) * QUESTIONS_PER_PAGE
  end = start + QUESTIONS_PER_PAGE

  questions = [question.format() for question in selection]
  current_questions = questions[start:end]

  return current_questions


def create_app(test_config=None):
  # create and configure the app
  app = Flask(__name__)
  app.secret_key = "super secret key"
  setup_db(app)
  CORS(app)

  @app.after_request
  def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,true')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

  '''
  @TODO: 
  Create an endpoint to handle GET requests 
  for all available categories.
  '''
  @app.route('/categories')
  def fetch_categories():
    selection = Category.query.order_by(Category.id).all()
    categories = [category.format() for category in selection]

    if len(categories) == 0:
      abort(404)
      
    return jsonify({
      'success': True,
      'categories': categories,
      'total_categories': len(Category.query.all())
    })

  '''
  @TODO: 
  Create an endpoint to handle GET requests for questions, 
  including pagination (every 10 questions). 
  This endpoint should return a list of questions, 
  number of total questions, current category, categories. 

  TEST: At this point, when you start the application
  you should see questions and categories generated,
  ten questions per page and pagination at the bottom of the screen for three pages.
  Clicking on the page numbers should update the questions. 
  '''
  @app.route('/questions')
  def fetch_questions():
    searchTerm = request.args.get('search-term', '', type=str)
    selection = Question.query.filter(Question.question.ilike('%' + searchTerm + '%')).order_by(Question.id).all()
    current_questions = paginate_questions(request, selection)
    categories = [category.format() for category in  Category.query.order_by(Category.id).all()]
    
    if len(current_questions) == 0:
      abort(404)
      
    return jsonify({
      'success': True,
      'questions': current_questions,
      'categories': categories,
      'current_category': 'null',
      'total_questions': len(Question.query.all())
    })


  '''
  @TODO: 
  Create an endpoint to DELETE question using a question ID. 

  TEST: When you click the trash icon next to a question, the question will be removed.
  This removal will persist in the database and when you refresh the page. 
  '''

  @app.route('/questions/<int:question_id>', methods=['DELETE'])
  def delete_book(question_id):
    try:
      question = Question.query.filter(Question.id == question_id).one_or_none()

      if question is None:
        abort(404)

      question.delete()

      return jsonify({
        'success': True,
        'deleted': question_id,
        'total_questions': len(Question.query.all())
      })

    except:
      abort(422)


  '''
  @TODO: 
  Create an endpoint to POST a new question, 
  which will require the question and answer text, 
  category, and difficulty score.

  TEST: When you submit a question on the "Add" tab, 
  the form will clear and the question will appear at the end of the last page
  of the questions list in the "List" tab.  
  '''

  @app.route('/questions', methods=['POST'])
  def create_book():
    body = request.get_json()

    try:
      question = Question(
        question = body.get('question', None),
        answer = body.get('answer', None),
        difficulty = body.get('difficulty', None),
        category = body.get('category', None) 
      )

      db.session.add(question)
      db.session.commit()

      return jsonify({
        'success': True,
        'created': question.id,
      })

    except:
      db.session.rollback()
      abort(422)
    
    finally:
      db.session.close()

  '''
  @DONE: 
  Create a GET endpoint to get questions based on category. 

  TEST: In the "List" tab / main screen, clicking on one of the 
  categories in the left column will cause only questions of that 
  category to be shown. 
  '''

  @app.route('/categories/<int:category_id>/questions')
  def fetch_questions_by_category_id(category_id):
    selection = Question.query.filter_by(category=category_id).order_by(Question.id).all()
    questions = paginate_questions(request, selection)
    categories = [category.format() for category in  Category.query.order_by(Category.id).all()]
    
    if len(questions) == 0:
      abort(404)
      
    return jsonify({
      'success': True,
      'questions': questions,
      'categories': categories,
      'current_category': 'null',
      'total_questions': len(Question.query.all())
    })

  '''
  @TODO: 
  Create a POST endpoint to get questions to play the quiz. 
  This endpoint should take category and previous question parameters 
  and return a random questions within the given category, 
  if provided, and that is not one of the previous questions. 

  TEST: In the "Play" tab, after a user selects "All" or a category,
  one question at a time is displayed, the user is allowed to answer
  and shown whether they were correct or not. 
  '''

  @app.route('/quizzes', methods=['POST'])
  def play_quiz():

    body = request.get_json()
    app.logger.info(body)

    if 'quiz_category' in body:
      category = body.get('quiz_category', None)
      # category = category.get('id', None)
      app.logger.info(category['id'])
    if 'previous_questions' in body:
      previous_questions = body.get('previous_questions', None)

    if int(category['id']) != 0:
      question = Question.query.filter_by(category=category['id']).filter(Question.id.notin_(previous_questions)).order_by(func.random()).first()
    else:
      question = Question.query.filter(Question.id.notin_(previous_questions)).order_by(func.random()).first()
    
    if question is None:
      abort(404)

    question = question.format()

    return jsonify({
      'success': True,
      'question': question
    })



  '''
  @TODO: 
  Create error handlers for all expected errors 
  including 404 and 422. 
  '''
  
  @app.errorhandler(404)
  def not_found(error):
     return jsonify({
        "success": False, 
        "error": 404,
        "message": "Not found"
     }), 404

  @app.errorhandler(422)
  def unprocessable(error):
    return jsonify({
      "success": False, 
      "error": 422,
      "message": "Unprocessable"
      }), 422

  @app.errorhandler(400)
  def bad_request(error):
    return jsonify({
      "success": False, 
      "error": 400,
      "message": "Bad request"
      }), 400

  return app

    