from flask import render_template, jsonify, request
from server import *

@server.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@server.route('/api/tags/tree', methods=['GET'])
def get_tags_tree():
    return jsonify(Tags.get_tree())

@server.route('/api/tags/file/<file>', methods=['GET'])
def get_file_tags(file):
    return jsonify(Files.tags(file))

@server.route('/api/files', methods=['GET']) 
def get_all_files():
    return jsonify(Files.all())

@server.route('/api/files/search/', methods=['GET']) 
def get_files():
    tags_list = request.args.get('tags')
    if not tags_list:
        tags_list = []
    return jsonify(Files.get_by_tags(tags_list))

@server.route('/api/tags', methods=['GET'])
def all_tags():
    return jsonify(Tags.all())

@server.route('/api/groups', methods=['GET'])
def all_groups():
    return jsonify(Groups.all())