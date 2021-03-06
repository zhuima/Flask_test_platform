# -*- coding: UTF-8 -*-
import json
import os
from urllib.parse import quote

from flask import Blueprint, request, make_response, send_from_directory
from flask_restful import Resource, Api, reqparse, fields
from werkzeug.utils import secure_filename

from com.common.aesUtil import AesUtil
from com.common.excelUtil import ExcelOperate
from com.common.getPath import Path
from com.common.uploadUtil import FileUpload
from com.service.api_manger import ApiMangerOperate
from com.service.dashboard import ContCase
from com.service.executeCase import ExecuteCase
from com.service.files_manger import FilesManager
from com.service.moker import ServiceOperate
from com.service.task_schedul import TaskSchedul
from com.service.test_case import TestCaseOperate
from com.service.test_report import TestReportOperate
from com.service.timeTask import TaskOperate
from com.service.user import UserOperate

apis = Blueprint('apis', __name__)
api = Api(apis)

resource_fields = {
    'body': fields.String,
    'result': fields.String
}

"""
系统用户处理
"""


class user(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('username', type=str, help='Rate to charge for this resource')
        self.parser.add_argument('password', type=str, help='Rate to charge for this resource')
        self.parser.add_argument('token', type=str, help='Rate to charge for this resource')
        self.ags = self.parser.parse_args()

    def get(self):
        result = UserOperate().get_user(self.ags['username'])
        if result is not None:
            username = AesUtil().decypt(self.ags['token']).replace(str(result['password']), '')
            if username == self.ags['username']:
                return {'status': True}
            return {'status': False}
        else:
            return {'status': False}

    def post(self):
        result = UserOperate().get_user(self.ags['username'])
        if result is not None and self.ags['password'] == str(result['password']):
            return {'login': True, 'token': AesUtil().encypt(str(result['user']) + str(result['password']))}, 200
        else:
            return {'login': False, 'token': None}, 200


"""
模拟服务，接口处理
"""


class services(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('service_name', type=str, help='Rate to charge for this resource')
        self.parser.add_argument('service_type', type=str, help='Rate to charge for this resource')
        self.parser.add_argument('data', type=str, help='Rate to charge for this resource')
        self.parser.add_argument('operate', type=str, help='Rate to charge for this resource')
        self.parser.add_argument('status', type=str, help='Rate to charge for this resource')
        self.parser.add_argument('user', type=str, help='Rate to charge for this resource')
        self.ags = self.parser.parse_args()

    def get(self):
        data = ServiceOperate().get_moker_list()
        result = {"data": data}
        return result

    def post(self):
        result = {"message": None}
        if (self.ags['service_name'] is not None):
            if (self.ags['operate'] == 'delete'):
                result = ServiceOperate().del_item(self.ags['service_name'])
                return result
            elif (self.ags['operate'] == 'add'):
                result = ServiceOperate().add_service(
                    {'service_name': self.ags['service_name'], 'type': self.ags['service_type'],
                     'data': self.ags['data'], 'path': '/moker/apis/' + self.ags['service_name'],
                     'status': self.ags['status'], 'user': self.ags['user']})
                return result
            elif (self.ags['operate'] == 'update'):
                result = ServiceOperate().update_service(
                    {'service_name': self.ags['service_name'], 'type': self.ags['service_type'],
                     'data': self.ags['data'], 'path': '/moker/apis/' + self.ags['service_name'],
                     'status': self.ags['status'], 'user': self.ags['user']})
                return result
        return result


"""
接口管理，增删改查
"""


class api_manger(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('api_name', help='Rate to charge for this resource')
        self.parser.add_argument('model', type=str, help='Rate to charge for this resource')
        self.parser.add_argument('type', type=str, help='Rate to charge for this resource')
        self.parser.add_argument('path', type=str, help='Rate to charge for this resource')
        self.parser.add_argument('headers', type=str, help='Rate to charge for this resource')
        self.parser.add_argument('need_token', type=str, help='Rate to charge for this resource')
        self.parser.add_argument('status', type=str, help='Rate to charge for this resource')
        self.parser.add_argument('mark', type=str, help=' Rate to charge for this resource')
        self.parser.add_argument('user', type=str, help='Rate to charge for this resource')
        self.parser.add_argument('operate', type=str, help='Rate to charge for this resource')
        self.ags = self.parser.parse_args()

    def get(self):
        data = ApiMangerOperate().get_list()
        result = {"data": data}
        return result

    def post(self):
        result = {"message": None}
        if (self.ags['api_name'] is not None):
            if (self.ags['operate'] == 'delete'):
                result = ApiMangerOperate().del_item(self.ags['api_name'])
                return result
            elif (self.ags['operate'] == 'add'):
                result = ApiMangerOperate().add_apis(self.ags)
                return result
            elif (self.ags['operate'] == 'update'):
                result = ApiMangerOperate().update_apis(self.ags)
                return result
        return result


"""
接口管理批量新增、更新上传处理
"""


class ApiUpload(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('user', type=str, help='Rate to charge for this resource')
        self.ags = self.parser.parse_args()

    def get(self):
        return None

    def post(self):
        f = request.files['files']
        upload_path = os.path.join(Path().get_current_path(), 'static/uploads',
                                   secure_filename(f.filename))
        f.save(upload_path)
        result = ExcelOperate().get_excellist(upload_path)
        os.remove(upload_path)
        result = ApiMangerOperate().batch_operate(result, user=self.ags.user)
        return result


class test_case(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('case_name', help='Rate to charge for this resource')
        self.parser.add_argument('case_id', help='Rate to charge for this resource')
        self.parser.add_argument('servi_name', help='Rate to charge for this resource')
        self.parser.add_argument('api_id', help='Rate to charge for this resource')
        self.parser.add_argument('parameter', type=str, help='Rate to charge for this resource')
        self.parser.add_argument('result', type=str, help='Rate to charge for this resource')
        self.parser.add_argument('validation_type', type=str, help='Rate to charge for this resource')
        self.parser.add_argument('mark', type=str, help='Rate to charge for this resource')
        self.parser.add_argument('user', type=str, help='Rate to charge for this resource')
        self.parser.add_argument('operate', type=str, help='Rate to charge for this resource')
        self.ags = self.parser.parse_args()

    def get(self):
        data = TestCaseOperate().get_list()
        result = {"data": data}
        return result

    def post(self):
        result = {"message": None}
        if (self.ags['operate'] == 'delete'):
            result = TestCaseOperate().del_case(self.ags['case_id'])
            return result
        if (self.ags['case_name'] is not None):
            if (self.ags['operate'] == 'add'):
                result = TestCaseOperate().add_case(self.ags)
                return result
            elif (self.ags['operate'] == 'update'):
                result = TestCaseOperate().update_case(self.ags)
                return result
        return result


class TestCaseUpload(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('user', type=str, help='Rate to charge for this resource')
        self.ags = self.parser.parse_args()

    def get(self):
        return None

    def post(self):
        f = request.files['files']
        upload_path = os.path.join(Path().get_current_path(), 'static/uploads',
                                   secure_filename(f.filename))
        f.save(upload_path)
        result = ExcelOperate().get_excellist(upload_path)
        os.remove(upload_path)
        result = TestCaseOperate().batch_operate(result, user=self.ags.user)
        return result


class execute_case(Resource):
    # def __init__(self):
    #     self.parser = reqparse.RequestParser()
    #     self.parser.add_argument('data', type=str, help='Rate to charge for this resource')
    #
    #     self.ags = self.parser.parse_args()

    def get(self):
        data = TestCaseOperate().get_execute_list()
        result = {"data": data}
        return result

    def post(self):
        result = ExecuteCase().execute_cases(request.json)
        return result


class get_modellist(Resource):
    def get(self):
        result = ApiMangerOperate().get_model_list()
        return {"data": result}


class get_reportdata(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('source', type=str, help='Rate to charge for this resource')
        self.parser.add_argument('batchnumber', type=str, help='Rate to charge for this resource')
        self.parser.add_argument('creater', type=str, help='Rate to charge for this resource')
        self.parser.add_argument('executetype', type=str, help='Rate to charge for this resource')
        self.parser.add_argument('daterange', type=str, help='Rate to charge for this resource')
        self.parser.add_argument('type', type=str, help='Rate to charge for this resource')

        self.ags = self.parser.parse_args()

    def get(self):
        if self.ags['type'] == 'createrlist':
            result = TestReportOperate().get_createrlist()
            return {'data': result}
        else:
            result = TestReportOperate().get_report_data(self.ags)
            return result


class time_task(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('operate', type=str, help='Rate to charge for this resource')
        self.parser.add_argument('task_id', type=str, help='Rate to charge for this resource')
        self.parser.add_argument('task_name', type=str, help='Rate to charge for this resource')
        self.parser.add_argument('model', type=str, help='Rate to charge for this resource')
        self.parser.add_argument('trigger', type=str, help='Rate to charge for this resource')
        self.parser.add_argument('start_time', type=str, help='Rate to charge for this resource')
        self.parser.add_argument('frequency', type=str, help='Rate to charge for this resource')
        self.parser.add_argument('until', type=str, help='Rate to charge for this resource')
        self.parser.add_argument('user', type=str, help='Rate to charge for this resource')
        self.ags = self.parser.parse_args()

    def get(self):
        result = TaskSchedul().get_list()
        return {'message': True, 'data': result}

    def post(self):
        result = []
        if self.ags['operate'] == 'delete':
            result = TaskSchedul().del_item(self.ags['task_id'])
            return result
        elif self.ags['operate'] == 'add':
            result = TaskSchedul().add_task(self.ags)
            return result
        elif self.ags['operate'] == 'update':
            result = TaskSchedul().update_task(self.ags)
            return result


class scheduling(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('operate', type=str, help='Rate to charge for this resource')
        self.parser.add_argument('task_id', type=str, help='Rate to charge for this resource')
        self.ags = self.parser.parse_args()

    def get(self):
        result = TaskOperate().get_jobs()
        return {'message': True, 'data': result}

    def post(self):
        if self.ags['operate'] == 'add':
            result = TaskOperate().add_jobs()
            return {'message': result, 'data': "ok"}
        if self.ags['operate'] == 'delete':
            result = TaskOperate().remove_job(self.ags['task_id'])
            return {'message': result, 'data': "ok"}


class files_manager(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('user', type=str, help='Rate to charge for this resource')
        self.parser.add_argument('type', type=str, help='Rate to charge for this resource')
        self.parser.add_argument('remark', type=str, help='Rate to charge for this resource')
        self.parser.add_argument('fileid', type=str, help='Rate to charge for this resource')
        self.ags = self.parser.parse_args()

    def get(self):
        if self.ags['type'] == 'get':
            result = FilesManager().get_list()
            if result:
                return {'message': True, 'data': result}
            else:
                return {'message': False, 'data': None}
        elif self.ags['type'] == 'download':
            basename = FilesManager().get_file_name(self.ags['fileid'])
            file_path = os.path.join(Path().get_current_path(), 'static/filesmanager',
                                     basename)
            dir_path = os.path.join(Path().get_current_path(), 'static/filesmanager')
            if os.path.exists(file_path):
                response = make_response(send_from_directory(dir_path, basename, as_attachment=True))
                # response.headers["Content-Disposition"] = "; filename=%s;" % (str(self.ags['filename']))
                # response.headers["Content-Disposition"] = "attachment;filename*=UTF-8''{}"\
                #     .format(utf_filename=quote(self.ags['filename'].ecode('utf-8')))
                response.headers["Content-Disposition"] = \
                    "attachment;" \
                    "filename*=UTF-8''{utf_filename}".format(
                        utf_filename=quote(basename.encode('utf-8'))
                    )
                return response
            else:
                return None

    def post(self):
        if self.ags['type'] == 'upload':
            result = FileUpload().save_file(request.files['files'], 'static/filesmanager')
            if result:
                result['user'] = self.ags['user']
                result['remark'] = self.ags['remark']
                data = FilesManager().add_file(result)
                return {'message': data}
        elif request.json['type'] == 'delete':
            if FilesManager().del_items(json.loads(request.json['data'])):
                data = FileUpload().delete_files(json.loads(request.json['data']))
                return {'message': data}
        elif request.json['type'] == 'remark':
            data = FilesManager().batch_update(json.loads(request.json['data']))
            return {'message': data}


class dash_board(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('type', type=str, help='Rate to charge for this resource')
        self.ags = self.parser.parse_args()

    def get(self):
        if self.ags['type'] == 'api_model_data':
            result = ContCase().get_api_model()
            if result:
                return result
            else:
                return {'message': False, 'data': None}
        elif self.ags['type'] == 'case_model_data':
            result = ContCase().get_case_model()
            if result:
                return result
        elif self.ags['type'] == 'api_case_data':
            result = ContCase().get_api_case()
            if result:
                return result
        elif self.ags['type'] == 'case_pass_data':
            result = ContCase().get_case_pass()
            if result:
                return result


api.add_resource(user, '/user')
api.add_resource(services, '/service')
api.add_resource(api_manger, '/apimanager')
api.add_resource(test_case, '/testcase')
api.add_resource(ApiUpload, '/apiupload')
api.add_resource(TestCaseUpload, '/testcaseupload')
api.add_resource(execute_case, '/executecase')
api.add_resource(get_modellist, '/modelist')
api.add_resource(get_reportdata, '/report')
api.add_resource(time_task, '/task')
api.add_resource(scheduling, '/scheduling')
api.add_resource(files_manager, '/filesmanager')
api.add_resource(dash_board, '/dashboard')
