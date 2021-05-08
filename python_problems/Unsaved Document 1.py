##############################################################################
#
# ZeOmega LLC license
# Copyright (c) 2009 ZeOmega LLC
# http://www.zeomega.com
# All rights reserved.
#
# ZeOmega software [both binary and source (if released)] (hereafter,
# Software) is intellectual property owned by ZeOmega LLC is copyright of
# ZeOmega LLC in all countries in the world, and ownership remains with
# ZeOmega LLC The Software is protected by the copyright laws of the United
# States and international copyright treaties.  Licensee is not allowed to
# distribute the binary and source code (if released) to third parties.
# Licensee is not allowed to reverse engineer, disassemble or decompile code,
# or make any modifications of the binary or source code, remove or alter any
# trademark, logo, copyright or other proprietary notices, legends, symbols,
# or labels in the Software.  Licensee is not allowed to sub-license the
# Software or any derivative work based on or derived from the Software.
# Neither the names of ZeOmega LLC , nor the names of its contributors may be
# used to endorse or promote products derived from this Software without
# specific prior written permission.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL THE
# CONTRIBUTORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# WITH THE SOFTWARE.
#
##############################################################################
"""
"""
import sys
import traceback
import copy
import simplejson as json
import xlrd
import re
import tempfile
import constants
import os
import os.path
import ast

from urllib import quote, unquote

from App.class_init import InitializeClass
from App.special_dtml import DTMLFile
from AccessControl import ClassSecurityInfo
from OFS.Folder import Folder

from datetime import datetime, timedelta
from mx.DateTime import DateTime as mx_date_time, RelativeDateTime

from Products.ZeUtil import fstozodb
from Products.ZeSentinel.models import Decisiontable
from Products.ZeSentinel.utils import Spreadsheet, get_base_external_cd
from Products.ZeSentinel.excel_export import action_export, rule_export, rule_set_export, assessment_rule_set_export, reference_table_export, decision_table_export

from Products.ZeJiva.config import zesql_binding_placeholder_begin, zesql_binding_placeholder_end

from permissions import controller_permissions
from constants import SE_EVENT_STATE_OPEN

from .models import *
from Products.ZeUtil.html_normalizer import normalize_form
manage_addZeSentinelCtrlForm = DTMLFile('dtml/ZeSentinelCtrl', globals())

re_exp = "[$!@#^*()`~;:<>?/,_\"]"

def manage_addZeSentinelCtrl(self, id, REQUEST=None):
    """
    Creates Sentinel Rule instance
    """

    sentinel_ctrl = ZeSentinelCtrl(id)
    self._setObject(id, sentinel_ctrl)

    if REQUEST is not None:
        return self.manage_main(self, REQUEST)

class ZeSentinelCtrl(Folder):
    """
    Sentinel Controller class
    """

    meta_type = "ZeSentinel Controller"
    security = ClassSecurityInfo()
    security.declareObjectProtected('Access contents information')

    def __init__(self, id):
        self.id = id
        self.title = 'ZeSentinel Controller'

    def manage_afterAdd(self, item, container):
        """
        This method creates ZeSentinel Ctrl folder and
        a views folder inside this Sentinel folder.

        @param item : item to be added
        @param container : context object

        """
        view_path = 'ZeSentinel/views'
        fstozodb.addDirectory(self,dir_name = 'views',dir_path = view_path)
        self.ZeUtil.setDefaultPermission(self, controller_permissions)
        return "done"

    ###############Rule code starts from here##################

    def getRuleTypes(self):
        """
        @description : Method to get rule types
        @return : return description of rule types from the config file(constants)
        """
        return constants.RULE_TYPE

    def getRuleExecutionTypes(self):
        """
        @description : Method to get rule execution types
        @return : return description of rule execution types 
                  from the config file(constants)
        """
        return constants.RULE_EXECUTION_TYPE

    def getEventTitles(self):
        """
        @description : Method to get event titles
        @return : return list of dictonaries containing cd and description of event titles.
        """
        return self.Sentinel.SentinelModel.selectEventTypes().dictionaries()

    def getRuleCategory(self):
        """
        @description : Method to get rule category
        @return : return rule category from table
        """
        return self.Sentinel.SentinelModel.selectRuleCategory().dictionaries()

    # we need clarification
    def addRuleActions(self, ruleId, actionIdList, user_id, exec_group):
        """
        This method is used to add rule actions

        NB: the isAction column is being removed.

        """
        if type(actionIdList) == type('string'):
            actionIdList = [actionIdList]

        entity_active = 'Y'
        priority = 0
        for eachActionId in actionIdList:
            self.Sentinel.SentinelModel.insertRuleAction(rule_id=ruleId,
                                                         action_id=eachActionId,
                                                         user_id=user_id,
                                                         priority = priority,
                                                         exec_group=exec_group
                                                         )
            priority=priority+1

    # we need clarification
    def addRuleCriteria(self, rule_id, prefix_op, suffix_op, criteria_ids,exec_group):
        """
        @description : This method is used to add all Criteria for the rule
        @param rule_id: Rule Id param is used for adding Criteria
        @param prefix_op : each criteria is enclosed with prefix operator n suffix operator ,  prefix operators are ('(',..)
        @param suffix_op : each criteria is enclosed with prefix operator n suffix operator , Suffix operator are (')','AND)','OR)')
        @param criteria_ids : passing criteria_ids for the rule id
        """
        try:
            user_id = int(self.cms.ZeUser.Model.getLoggedinUserIdn())
        except:
            user_id = 3
        if type(criteria_ids) == type('string'):
            criteria_ids=[criteria_ids]

        if type(prefix_op) == type('string'):
            prefix_op=[prefix_op]

        if type(suffix_op) == type('string'):
            suffix_op = [suffix_op]
        priority = 0
        for each in criteria_ids:

            index = criteria_ids.index(each)
            try:
                new_prefix_op = prefix_op[index]
            except Exception, e:
                new_prefix_op = ''

            try:
                new_suffix_op = suffix_op[index]
            except Exception, e:
                new_suffix_op = ''
            self.Sentinel.SentinelModel.addCriteriasForRule(rule_id, new_prefix_op,
                                                            new_suffix_op, each,priority,user_id,exec_group)
            priority = priority+1
        return

    ##########Event code starts from here###############

    def getValidEventStates(self):
        """
        @description : Method to get valid event state
        @return : return list of event states.
        """

        return constants.VALID_EVENT_STATES

    def getAlertsToList(self):
        """
        @description : Method to get alert to list ie Nurse, Episode, Claimant which is defined in sentinel_constants
        @return : This function returns alert To list ie Nurse, Episode,Claimant which is defined in sentinel_constants.
        """
        return constants.alert_to_list

    # We need calrification.
    def showTray(self):
        """ """
        request = self.REQUEST
        #res_set = self.Alerts.Model.getAlertsAtDifferentLevels(user_idn=self.ZeUser.Model.getLoggedinUserIdn(),no_of_records='')
        #res_set = self.ZeUtil.getDictionaryOfResultSet(res_set)
        res_set = self.SentinelModel.selectTrayRecords(user_idn=self.ZeUser.Model.getLoggedinUserIdn())
        res_set = self.ZeUtil.getDictionaryOfResultSet(res_set)
        tray_list_value = []
        if res_set:
            for each in res_set:
                tray_list_value.append(each['SHOW_TRAY'])
            if 'Y' in tray_list_value:
                return 'Y'
            else:
                return 'N'
        else:
            return 'N'

    # We need calrification.
    def getTrayRecords(self):
        """ returns test page"""
        request = self.REQUEST
        res_set = self.SentinelModel.selectTrayRecords(user_idn=self.ZeUser.Model.getLoggedinUserIdn())
        res_set = self.ZeUtil.getDictionaryOfResultSet(res_set)
        return len(res_set)

    # We need calrification.
    def showActionPageForAssessment(self):
        """ returns action page for assessement
            @return : This function returns dtml file
        """
        request = self.REQUEST
        dtml_document = getattr(self.views, 'ace_action')
        return dtml_document(self.views, REQUEST = request)

    # We need calrification.
    def getActionDetailsForACE(self, actionScript=''):
        """
        Returns list containing dictionaries of action details (id, title, description ,script name and parameter details)
        for Assessment.
        """
        request = self.REQUEST
        action_script = request.get('filter_action_script',actionScript)

        raw_action_details_list = []
        action_details_recordset = self.Sentinel.SentinelModel.selectDetailedActionsForACE(action_script = action_script)

        if action_details_recordset:
            for each in action_details_recordset.dictionaries():
                raw_action_details_list.append(each)
        action_details_list = []
        processed_actions = {}
        for eachActionRecord in raw_action_details_list:
            actionid = eachActionRecord['IDN']
            if actionid not in processed_actions.keys():
                processed_actions[actionid] = {}
                processed_actions[actionid]['ACTION_ID'] = actionid
                processed_actions[actionid]['ACTION_TITLE'] = eachActionRecord['ACTION_TITLE']
                processed_actions[actionid]['ACTION_DESCRIPTION'] = eachActionRecord['ACTION_DESCRIPTION']
                processed_actions[actionid]['ACTION_SCRIPT_NAME'] = eachActionRecord['ACTION_SCRIPT_NAME']
                processed_actions[actionid]['parameter_details'] = []
                if eachActionRecord['PARAM_NAME'] and eachActionRecord['PARAM_VALUE']:
                    processed_actions[actionid]['parameter_details'].append( '%s=%s' % (eachActionRecord['PARAM_NAME'], eachActionRecord['PARAM_VALUE']))
            else:
                processed_actions[actionid]['parameter_details'].append( '%s=%s' % (eachActionRecord['PARAM_NAME'], eachActionRecord['PARAM_VALUE']))

        if processed_actions:
            action_details_list = processed_actions.values()
        return action_details_list

    def getCriteriaTitle(self, criteria_id=0):
        """
        @description : Method to get criteria title
        @param : criteria_id {int} criteria id
        @return : criteria title
        """
        request = self.REQUEST
        criteria_id = criteria_id.split(',')
        criteriatitle=[]
        for i in criteria_id:
            criteria_title = self.Sentinel.SentinelModel.getClauseValuesByTitleOrId(clause_id=i)
            for ctitle in criteria_title:
                criteriatitle.append(quote(ctitle['CRITERIA_TITLE'])+'$$'+str(ctitle['SRE_CRITERIA_IDN'])+'$$'+str(ctitle['CRITERIA_TYPE']))
        return '@@'.join(criteriatitle)


    def getActionTitle(self, action_id='0'):
        """
        @description : Method to get action title
        @param : action_id {string} action id
        @return : action title
        """
        request = self.REQUEST
        if action_id=='0':
            action_id=[action_id]
        else:
            action_id = action_id.split(',')

        actiontitle=[]
        for i in action_id:
            action_title = self.Sentinel.SentinelModel.getActionRecords(action_id=i)
            for atitle in action_title:
                actiontitle.append(quote(atitle['action_title'])+'$$'+str(atitle['SRE_ACTION_IDN']))
        return '@@'.join(actiontitle)

    def readExcelFile(self, sh, ref_table_id='', append_flag='', update_flag='N'):
        """
        @description : Method to read excel file
        @param : sh - <xlrd file object>
        @param : ref_Table_id {int} reference table id
        @param : append_flag {string} append flag either 'Y/N'
        """

        headerValues = []
        try:
            user_id = int(self.cms.ZeUser.Model.getLoggedinUserIdn())
        except:
            user_id = 3
        try:
            headerRow = sh.row_values(0)
            pos=1
            mis_match_count = 0
            mis_match_header = ''
            if append_flag == 'Y' or update_flag == 'Y':
                header_name = self.Sentinel.SentinelModel.getColumnValues(ref_table_idn=ref_table_id)
                for i in (range(headerRow.__len__())):
                    if headerRow[i] == '':
                        del headerRow[i]
                if header_name.__len__() != headerRow.__len__():
                    return'%s@@%s'%('2',mis_match_header)

            if append_flag == 'Y' :
                max_row_id = self.Sentinel.SentinelModel.selectMaxRefRowIdForTable(ref_table_id=ref_table_id)
                max_row_id = max_row_id.dictionaries()[0]['MAX_ROW_ID']
                if not max_row_id:
                    max_row_id = 0

            for headerCell in headerRow:
                # insert header here.....
                # get Id and append to list.
                if headerCell != '': # Checking Header is Empty or Not.
                    if append_flag == 'Y' or update_flag == 'Y':
                        for res in header_name:
                            if pos == res['POSITION']:
                                col_name = self.ZeUtil.encode(headerCell)
                                if res['COLUMN_NAME'] == col_name.strip():
                                    headerValues.append(res['COLUMN_ID'])
                                else:
                                    mis_match_count = mis_match_count + 1
                                    mis_match_header+=','+col_name
                        pos = pos+1

                    elif update_flag == 'N':
                        header_id = self.Sentinel.SentinelModel.insertReferenceColumn(sre_ref_table_idn=ref_table_id,ref_column_name=str(headerCell).strip(),ref_column_pos=pos,user_id=user_id)
                        header_id = header_id[0][0]
                        headerValues.append(header_id)
                        pos = pos+1
                        print "Header Cell... value == %s \n" % (headerCell)

            if mis_match_count == 1:
                mis_match_header = mis_match_header[1:]+' '+'header'
            if mis_match_count == 2:
                mis_match_header = mis_match_header[1:]+' '+'header(s)'
            if 1 <= mis_match_count:
                return'%s@@%s'%('2',mis_match_header)
            else:
                if update_flag == 'Y':
                    self.Sentinel.SentinelModel.deActivateRefValue(ref_table_id=ref_table_id, user_idn=user_id)
                for traverse_row in range(1,sh.nrows):
                    types,values = sh.row_types(traverse_row),sh.row_values(traverse_row)
                    header_indx = 0
                    for indx in range(0,len(values)):
                        if header_indx<len(headerRow): # Checking How many header.
                            if headerRow[header_indx] != '': # Checking Header value is Empty or Not.
                                cell_value = self.formatrow(types[indx], values[indx], 0)
                                try:
                                    cell_value = str(cell_value)
                                except UnicodeError:
                                    chars = []
                                    for char in values[indx]:
                                        try:
                                            chars.append(char.encode('ascii', 'strict'))
                                        except UnicodeError:
                                            chars.append('&#%i;' % ord(char))
                                    cell_value = ''.join(chars)
                                if cell_value == '':
                                    cell_value = 'No Value'
                                ref_column_id = headerValues[indx]
                                if append_flag == 'Y':
                                    row_id = max_row_id + traverse_row
                                    header_id = self.Sentinel.SentinelModel.insertReferenceTableValue(ref_table_id,ref_column_id,str(cell_value).strip(),user_id,row_id=row_id)
                                else:
                                    header_id = self.Sentinel.SentinelModel.insertReferenceTableValue(ref_table_id,ref_column_id,str(cell_value).strip(),user_id,row_id=traverse_row)
                            header_indx+=1
        except Exception, e:
            print e
        return

    def formatrow(self, type, value, wanttupledate):
        """
        @description : Method to Internal function used to clean up the incoming excel data
        @param : type {string} type of cell.
        @param : value {string} cell value.
        @param : wanttupledate {string} date.
        """
        ##  Data Type Codes:
        ##  EMPTY 0
        ##  TEXT 1 a Unicode string
        ##  NUMBER 2 float
        ##  DATE 3 float
        ##  BOOLEAN 4 int; 1 means TRUE, 0 means FALSE
        ##  ERROR 5
        if type == 3:
            datetuple = xlrd.xldate.xldate_as_tuple(value,0)
            if wanttupledate:
                value = datetuple
            else:
                # time only no date component
                if datetuple[0] == 0 and datetuple[1] == 0 and \
                   datetuple[2] == 0:
                    value = "%02d:%02d:%02d" % datetuple[3:]
                # date only, no time
                elif datetuple[3] == 0 and datetuple[4] == 0 and \
                     datetuple[5] == 0:
                    value = "%04d/%02d/%02d" % datetuple[:3]
                else: # full date
                    value = "%04d/%02d/%02d %02d:%02d:%02d" % datetuple
        elif type == 5:
            value = xlrd.error_text_from_code[value]

        return value

    def runEngine(self): #FOR ROOPESH ##################################################################################################33
        """  """
        from .engine.dbload2 import setup

        setup(self)
        return "Execution Complete - Examine the Zope Log"

    def getEntityValues(self):
        """
        @description : Method to get the Entities from code table

        @return : return entity values
        """
        rs = self.Sentinel.SentinelModel.getEntityValues().dictionaries()
        return rs

    def getRuleActionCriteriaDetails(self,rule_id,from_template = 'N'):
        """
        @description : Method to display action and criteria values in  the respective blocks in edit rule page

        @param : rule_id {int} rule id
        @param : from_template {string} template flag either 'N/Y'.
        @return : return rule action and criteria details.
        """
        #print rule_id
        criteriaList = self.Sentinel.SentinelModel.getCriteriasForRule(rule_id).dictionaries()# get criteria results
        actions = self.Sentinel.SentinelModel.getRuleActionMasterDetails(rule_id).dictionaries()# get action results
        execgroupno = []
        noelseaction = 1
        # seperate results based on exec group
        for i in criteriaList:
            i['type'] = 'criteria'
            if i['EXEC_GROUP'] not in execgroupno:
                execgroupno.append(i['EXEC_GROUP'])
        for i in actions:
            if i['EXEC_GROUP'] not in execgroupno:
                i['type'] = 'elseaction'
            else:
                i['type'] = 'action'
        for act in actions:
            if 'elseaction' in act.values():
                noelseaction = 0
        lst = actions+criteriaList
        criteria_count = len(criteriaList)
        action_count = len(actions)
        # To seperate blocks of else if based on exec_group
        main_list = []
        dict_main ={}
        elsegrp = []
        for each in lst:
            if each['EXEC_GROUP'] in execgroupno:
                l2=[]
                if each['EXEC_GROUP'] in dict_main:
                    dict_main[each['EXEC_GROUP']].append(each)
                else:
                    l2.append(each)
                    dict_main[each['EXEC_GROUP']] =l2

            else:
                elsegrp.append(each)
                dict_main[each['EXEC_GROUP']] = elsegrp
        if noelseaction:
            res = dict_main.values()
            res.append([])
            return_value = (res,criteria_count,action_count)

        else:
            return_value = (dict_main.values(),criteria_count,action_count)
        if from_template == 'Y':
            return_value = return_value[0]
        return return_value

    # we need clarification
    def processRulesForEvent(self):  # DOES NOT SEEM TO BE USED ANYWHERE !!!
        """
        @description : This methods evaluates a rule using the new engine.
        """

        from .Load_Entities import RulesEngine
        
        ename    = self.REQUEST.get('event_name', '')
        rtype    = self.REQUEST.get('rule_type', 'Batched')
        rcatcode = self.REQUEST.get('rule_category', None)

        engine = RulesEngine()
        engine.run_event(self, event=ename, rule_type=rtype, rule_category=rcatcode, extra_arg='hello')
        message = 'Successfully processed rules'
        msg_type = "Info"

        self.REQUEST.set('info_alert', message)
        return msg_type + "," + message

    def loadEntities(self): #FOR ROOPESH ##################################################################################################33
        """  """
        from .Load_entities.load_entitydefs import load_entitydefs

        load_entitydefs(self)
        return "Execution Complete - Examine the Zope Log"

    def convertValueForXl(self, value):
        """
        @description : This methods used to convert value for xl.

        @param : value {string} value.
        @return - return value appended with double quotes for criteria value
        as double quotes are converted to single quote in excel
        """
        try:
            if type(int(value) == 'int'):
                value = int(value)
        except:
            if re.search('^\(',value) and re.search('\)$',value):
                value = value
            elif re.search('^\'',value):
                value = "'"+value
        return value

    def getCriteriaCondResults(self, i_criteria_id):
        """
        @description : This methods used to get criteria redults.

        @param : i_criteria_id {int} criteria id.
        @return : return criteria conditional results
        """
        request = self.REQUEST
        result_set = self.Sentinel.SentinelModel.getcriteriaConditionSet(i_criteria_id).dictionaries()
        return result_set

    ####JIVA5 UI Refactoring related code starts here#####

    #############Sentinel configuration code starts from here##################

    security.declareProtected('Ze Sentinel ViewEngineLNP', 'getSentinelEngineLeftNav')
    def getSentinelEngineLeftNav(self):
        """
        @description : This methods used to return left navigation for engine.
        @return: Returns the page with left navigation for Nurse Manage Episodes
        """
        REQUEST = self.REQUEST
        dpage = self.views.sentinel_left_navigation
        return dpage(self.views, REQUEST=self.REQUEST,tag_name='engine')

    security.declareProtected('Ze Sentinel ViewLogLNP', 'getSentinelLogLeftNav')
    def getSentinelLogLeftNav(self):
        """
        @description : This methods used to return left navigation for log.
        @return: Returns the page with left navigation for Nurse Manage Episodes
        """
        REQUEST = self.REQUEST
        dpage = self.views.sentinel_left_navigation
        return dpage(self.views, REQUEST=self.REQUEST,tag_name='log')

    security.declareProtected('Ze Sentinel ViewConfigLNP', 'getSentinelConfigLeftNav')
    def getSentinelConfigLeftNav(self):
        """
        @description : This methods used to return left navigation for configuration.
        @return: Returns the page with left navigation for Nurse Manage Episodes
        """
        REQUEST = self.REQUEST
        dpage = self.views.sentinel_left_navigation
        return dpage(self.views, REQUEST=self.REQUEST,tag_name='config')

    def getSentinelEngineTreeStructure(self):
        """
        @description : This method used to get engine tree structure.
        @return: Returns the page with left navigation for Nurse Manage Episodes
        """
        request = self.REQUEST
        event_type=''
        new_event_recordset = self.Sentinel.SentinelModel.selectEventTitlesByEventType(event_type)
        event_list=[]
        action_list=[]
        rule_list=[]
        for event_list_rec in new_event_recordset:
            data={}
            data['type'] = 'text'
            data['etype'] = event_list_rec['CD']
            data['html'] = event_list_rec['NAME']
            data['label'] = event_list_rec['NAME']
            data['treetype'] = 'Events'
            data['renderHidden'] = 'true'
            event_list.append(data)
        event_status_list = self.SentinelModel.selectCountofEventStatus()
        action_scripts = self.SentinelEngine.SentinelActions.action_registry
        for action_list_rec in action_scripts:
            data={}
            data['type'] = 'text'
            data['script_type'] = action_scripts[action_list_rec]
            data['html'] = action_list_rec
            data['label'] = action_list_rec
            data['renderHidden'] = 'true'
            action_list.append(data)
        action_list.sort()
        rule_cat_recordset = self.Sentinel.SentinelModel.selectRuleCategory()
        lst = []
        for rule_cat_list in rule_cat_recordset:
            data = {}
            data['type'] = 'text'
            data['html'] = rule_cat_list.IDN
            data['label'] = rule_cat_list.CTGY_CD
            data['renderHidden'] = 'true'
            rule_list.append(data)
        rule_list.sort()
        dpage = self.views.sentinel_engine_left_navigation
        return dpage(self.views,\
                     REQUEST=self.REQUEST,
                     event_status_list=event_status_list,
                     event_list=event_list,
                     action_list=action_list,
                     rule_list=rule_list)

    def getSentinelLeftNavSlot(self,tag_name):
        """
        @description : This method used to get left navigation slot.

        @param : tag_name {string} Represent tag name (engine/log/config).
        @return : return specific page.
        """

        if tag_name == 'engine': 
            nav_tree = [('event',['event_status','events']),
                        ('criteria',[]),
                        ('action',['actions']),
                        ('knowledge_base',['rule_business_process','ruleset_business_process'])
                        ]
            dpage = self.sentinel_engine_left_navigation
        if tag_name=='log':
            nav_tree = ''          
            dpage = self.views.sentinel_log_left_navigation
        if tag_name=='config':
            nav_tree = [('config_export',[]),('config_import',[]),('config_entities',[])]
            dpage = self.views.sentinel_config_left_navigation
        return dpage(self.views, REQUEST=self.REQUEST,
                     nav_tree=nav_tree)

    #############Sentinel Configuration code ends here######################

    def modifyUploadRefTable(self):
	
        """
        @description : This method to modify/upload reference table.
        Script to modify / upload reference table
        Read excel sheet
        1) Get Excel Sheet Name and add it to SRE_REFTABLE
        2) get headers and add it to SRE_REFCOLUMN as a value
                each hearder as on row in table
        3) SRE_REFVALUE each values with the ref column name
        Eg
        table name : assesment
        excel sheet
        HEARDER1        HEADER2         HEADER3
        one             two             three
        1one            1two            1three
        2one            2two            2three
        ========================================================
        SRE_REFTABLE
        ------------
        SRE_REFTABLE_IDN        REFTABLE_NAM
        1                       assesment
        SRE_REFCOLUMN
        -------------
        SRE_REFCOLUMN_IDN       SRE_REFTABLE_IDN        REFCOLUMN_NAME          REFCOLUMN_POS
        1                       1                       HEADER1                 1
        2                       1                       HEADER2                 2
        3                       1                       HEADER3                 3
        SRE_REFTABLE_VALUE
        ------------------
        INserting Column Wise
        SRE_REFVALUE_IDN        SRE_REFTABLE_IDN        SRE_REFCOLUMN_IDN       REFCOLUMN_VALUE
        1                       1                       1                       one
        2                       1                       1                       1one
        3                       1                       1                       2one
        4                       1                       2                       two
        5                       1                       2                       1two
        6                       1                       2                       2two
        7                       1                       3                       three
        8                       1                       3                       1three
        @return : return to reference result page.
        """
	import pdb;pdb.set_trace()
        request = self.REQUEST
        update_ref_table = request.get('update_ref_table','N')
        append_ref_table = request.get('append_ref_table','N')
        btw_sht_fail = 'N'
        upd_sheet_flag = 'Y'
        try:
            user_id = int(self.cms.ZeUser.Model.getLoggedinUserIdn())
        except:
            user_id = 3
        refName=request.get('ref_title').strip()
        #insert in to sre_ref_table
        # params : title ie table name
        try:
            uploaded_file = request.get('upload_ref', '')
            fname=r"%s" % str(uploaded_file.filename)
            ref_file_name = fname.split('\\')[-1]
            cwd = os.path.abspath(os.path.dirname(__file__))
            if not os.path.exists(cwd+'/reference_table'):
                os.mkdir(cwd+'/reference_table')
            ref_table_path = os.path.join(cwd, 'reference_table', ref_file_name)
            raw_file = uploaded_file.read()
            f = file(ref_table_path, 'wb')
            f.write(raw_file)                   # write text to file
            f.close()

            if not os.path.isfile(ref_table_path):
                raise NameError, "%s is not a valid filename" % ref_table_path
            wb = xlrd.open_workbook(ref_table_path)
            sheets = wb.sheet_names()
            # This Block is used to validate sheets are empty
            sheets_name = ''
            empty_sheet_name = []
            # This flag is used to check all the sheets are empty
            sheet_flag = 'N'
            count = 1
            title = ''
            title_count = 1
            for name in sheets:
                sh = wb.sheet_by_name(name)
                if upd_sheet_flag == 'Y':
                    refname = {True: refName+'_'+str(name), False: refName}\
                            [update_ref_table == 'N']
                    upd_sheet_flag = {True:'N', False:'Y'}\
                                   [update_ref_table == 'Y']
                    if refname.__len__() > 50:
                        title+='\n'+str(title_count)+'.'+self.ZeUtil.encode(name)+'$$'+refname
                        title_count+=1
                    if sh.nrows == 0:
                        sheets_name+=str(count)+'.'+self.ZeUtil.encode(name)+'~~~'
                        count+=1
                        empty_sheet_name.append(self.ZeUtil.encode(name))
                    else:
                        if 1 <= sh.nrows:
                            headerRow = sh.row_values(0)
                            for i in (range(headerRow.__len__())):
                                if headerRow[i] == '':
                                    sheets_name+=str(count)+'.'+self.ZeUtil.encode(name)+'~~~'
                                    count+=1
                                    empty_sheet_name.append(self.ZeUtil.encode(name))
                                    break
            #This block is used to check the Title Length
            if 1<title_count:
                return'%s@@%s'%('1',title)
            upd_sheet_flag = 'Y'
            # Update Reference Table
            if update_ref_table == 'Y' and count == 1:
                upd_ref_table_id = request.get('ref_table_id','')
                if append_ref_table == 'N':
                    request.set('info_alert', self.ZeUtil.getJivaMsg(msg_code = '712'))
                else:
                    request.set('info_alert', self.ZeUtil.getJivaMsg(msg_code = '745'))
                for i in sheets:
                    sh = wb.sheet_by_name(i)
                    if self.ZeUtil.encode(i) not in empty_sheet_name:
                        refname = {True: refName+'_'+str(i), False: refName}\
                                [update_ref_table == 'N']
                    # Modify Reference Table
                    # -- Suppose user having Multiple sheets then we will take (first sheet) of that Excel File
                        if upd_sheet_flag == 'Y':
                            upd_sheet_flag = {True:'N', False:'Y'}\
                                           [update_ref_table == 'Y']
                            refname = refname.strip()
                            if append_ref_table == 'N':
                                ref_table_id = upd_ref_table_id
                                sheet_flag = 'Y'
                                readFile = self.readExcelFile(sh, ref_table_id=ref_table_id, update_flag='Y')
                                if readFile:
                                    result = readFile.split('@@')
                                    # This Block is used validate mis match header.
                                    if result[0] == '2':
                                        return'%s@@%s'%(result[0],result[1])
                            else:
                                readFile = self.readExcelFile(sh, ref_table_id=upd_ref_table_id, append_flag='Y', update_flag='')
                                if readFile:
                                    result = readFile.split('@@')
                                    # This Block is used validate mis match header.
                                    if result[0] == '2':
                                        return'%s@@%s'%(result[0],result[1])
                                request.set('ref_tbl_id', upd_ref_table_id)
                                sel_value = self.addRefTable(ref_table_id=upd_ref_table_id)
                                return'%s@@%s'%(sel_value,sheets_name)
            else:
                request.set('info_alert', self.ZeUtil.getJivaMsg(msg_code = '693'))
                if update_ref_table == 'N':
                    for i in sheets:
                        sh = wb.sheet_by_name(i)
                        if self.ZeUtil.encode(i) not in empty_sheet_name:
                            refname = refName+'_'+str(i)
                            refname = refname.strip()
                            rs = self.Sentinel.SentinelModel.insertReferenceTable(\
                                refname,user_id)
                            ref_table_id = rs.dictionaries()
                            ref_table_id = ref_table_id[0]['SRE_REFTABLE_IDN']
                            sheet_flag = 'Y'
                            readFile = self.readExcelFile(sh,ref_table_id=ref_table_id)
                        else:
                            btw_sht_fail = 'Y'
        except Exception, e:
            return'%s@@%s'%('0','')
        # This block is used to check current upload Excel file is Error or Not.
        if sheet_flag == 'N':
            return'%s@@%s'%('0',sheets_name)
        else:
            request.set('ref_tbl_id', ref_table_id)
            sel_value = self.addRefTable(ref_table_id=ref_table_id)
            return'%s@@%s@@%s'%(sel_value,sheets_name,btw_sht_fail)

    def addRefTable(self,ref_table_id=''):
        """
        @description : This method to show modify reference table page.

        @param : ref_table_id {int} reference table id.
        @return : return modify reference table page.
        """
        request = self.REQUEST
        header = self.ZeUI.getHeader()
        footer = self.ZeUI.getFooter()
        dtml_document = getattr(self.views, 'modify_reference_table')
        return header+dtml_document(self.views,
                                    REQUEST=request,
                                    add_ref_tableid=ref_table_id
                                    )+footer

    def addDecisionTable(self,dec_table_id=None):
        """
        @description : This method to show modify decision table page.

        @param : dec_table_id {int} decision table id.
        @return : return modify decision table page.
        """
        request = self.REQUEST
        header = self.ZeUI.getHeader()
        footer = self.ZeUI.getFooter()
        dtml_document = getattr(self.views, 'modify_decision_table')
        return header+dtml_document(self.views,
                                    REQUEST=request,
                                    add_decision_tableid=dec_table_id
                                    )+footer


    def getreftablePage(self):
        """
        @description : This method to show upload reference table page.
        @return : return to reference table upload page
        """
        request = self.REQUEST
        header_type = ''
        if request.has_key('header_type'):
            header_type = request['header_type']
        header = self.ZeUI.getHeader(header_type)
        footer = self.ZeUI.getFooter(header_type)
        dtml_document = getattr(self.views, 'upload_referencetable_page')
        return header+dtml_document(self.views, REQUEST=request,add_ref_tableid='')+footer

    def getDecisionTablePage(self):
        """
        @description : This method to show upload decision table page.
        @return : return to Decision table upload page
        """
        request = self.REQUEST
        header = self.ZeUI.getHeader()
        footer = self.ZeUI.getFooter()
        dtml_document = getattr(self.views, 'upload_decision_table_page')
        return header+dtml_document(self.views, REQUEST=request,add_decision_tableid='')+footer

    def getDecisionTableResultPage(self,dec_table_idn=''):
        """
        @description : This method to get reference table result page.

        @return : returns reference table result page
        """
        request = self.REQUEST
        noResultMsg=self.ZeUtil.getJivaMsg(msg_code='627')
        node_count = request.get('number_node','')
        col_names = request.get('column_name','')
        if col_names:
            col_names = ast.literal_eval(col_names)
        if not dec_table_idn:
            dec_table_idn = request.get('dec_table_idn','')
        export_flag = request.get('export_flag','N')
        db_type = self.ZeUtil.isOracle()
        if db_type: # ORACLE Changes
            if export_flag == 'Y':
                row_id = '/table/row'
                tot_row = self.Sentinel.SentinelModel.selectDecisionTblColCount(dec_table_idn=int(dec_table_idn),row_id=repr(row_id))[0]['TOT_ROW']
                row_start = 1
                row_end = tot_row
                result_set = self.getDecisionTableInfo(dec_table_idn=dec_table_idn,row_id=row_id,db_type=db_type,row_start=row_start,row_end=row_end,order_by='ASC')
                result_len = len(result_set)
                col_names = result_set.tuples()[0]
                # Response redirected to the location of excel file in the zodb_repository
                excel_object_url = decision_table_export(self, result_set.tuples(), col_names)
                return request.RESPONSE.redirect(excel_object_url)
            else:
                if not node_count:
                    node_count = self.Sentinel.SentinelModel.selectDecisionTblColInfo(dec_table_idn=int(dec_table_idn),xml_path=repr('/table/row[1]'),row_block=repr('/row/*'))[0]['NUMBER_NODES']
                dec_table_name = request.get('dec_table_name','')
                I_CUR_PAGE = int(request.get('I_CUR_PAGE','1'))
                row_range = self.ZeUI.getPaginationStartEndRecords(cur_page=I_CUR_PAGE)
                row_index = []
                row_id = '/table/row'
                tot_row = self.Sentinel.SentinelModel.selectDecisionTblColCount(dec_table_idn=int(dec_table_idn),row_id=repr(row_id))[0]['TOT_ROW']
                #This Block used to NUmber of Records more than 10 Started Here
                if tot_row > 11:
                    if tot_row > row_range[1]:
                        row_start = tot_row - (row_range[1] - 1)
                        row_end = tot_row - (row_range[0] - 2)
                        for index in reversed(range(row_start,row_end)):
                            row_index.append(index)
                        row_end = row_end - 1
                    else:
                        row_start = 2
                        row_end = tot_row - (row_range[0] - 1)
                        for index in reversed(range(row_start,(row_end+1))):
                            row_index.append(index)
                else: #This Block used to NUmber of Records less than 10 Started Here
                    I_CUR_PAGE = 1
                    row_start = 2
                    row_end = tot_row + 1
                    for index in reversed(range(row_start,row_end)):
                        row_index.append(index)
                    row_end = row_end - 1
                if not row_index and tot_row > 11: #This block is used to suppose user delete middle of page then we are redirect to previous page.
                    I_CUR_PAGE = I_CUR_PAGE - 1
                    row_range = self.ZeUI.getPaginationStartEndRecords(cur_page=I_CUR_PAGE)
                    if tot_row > row_range[1]:
                        row_start = tot_row - (row_range[1] - 1)
                        row_end = tot_row - (row_range[0] - 2)
                        for index in reversed(range(row_start,row_end)):
                            row_index.append(index)
                        row_end = row_end - 1
                    else:
                        row_start = 2
                        row_end = tot_row - (row_range[0] - 1)
                        for index in reversed(range(row_start,(row_end+1))):
                            row_index.append(index)
                result_set = self.getDecisionTableInfo(dec_table_idn=dec_table_idn,row_id=row_id,db_type=db_type,row_start=row_start,row_end=row_end,node_count=int(node_count),order_by='DESC')
                result_len = len(result_set)
                if not col_names:
                    col_names = self.getDecisionTableInfo(dec_table_idn=dec_table_idn,row_id=row_id,db_type=db_type,row_start=1,row_end=1,node_count=int(node_count),order_by='DESC').tuples()[0]
                total_rec = tot_row-1
        else: # MSSQL Changes
            if export_flag == 'Y':
                result_set = self.getDecisionTableInfo(dec_table_idn=dec_table_idn,row_id='')
                result_len = len(result_set)
                col_names = result_set.tuples()[0]
                # Response redirected to the location of excel file in the zodb_repository
                excel_object_url = decision_table_export(self, result_set.tuples(), col_names)
                return request.RESPONSE.redirect(excel_object_url)
            else:
                if not node_count:
                    xml_path = "COUNT(DISTINCT 'col.value(''' + col.value('fn:local-name(.[1])', 'varchar(max)') + '[1]'', ''varchar(max)'') as '+ col.value('fn:local-name(.[1])', 'varchar(max)'))"
                    node_count = self.Sentinel.SentinelModel.selectDecisionTblColInfo(dec_table_idn=int(dec_table_idn),xml_path=xml_path,row_block=repr('/row/*'))[0]['NUMBER_NODES']
                dec_table_name = request.get('dec_table_name','')
                I_CUR_PAGE = int(request.get('I_CUR_PAGE','1'))
                row_range = self.ZeUI.getPaginationStartEndRecords(cur_page=I_CUR_PAGE)
                row_id = ''
                row_index = []
                tot_row = self.Sentinel.SentinelModel.selectDecisionTblColCount(dec_table_idn=int(dec_table_idn),row_id=repr('/row'))[0]['tot_row']
                #This Block used to NUmber of Records more than 10 Started Here
                if tot_row > 11:
                    row_start = tot_row - (row_range[1] - 1)
                    row_end = (tot_row - row_range[0] + 2)
                    for index in reversed(range(row_start,row_end)):
                        if index > 1:
                            row_id = row_id + '/row['+str(int(index))+']' + ','
                            row_index.append(index)
                else: #This Block used to NUmber of Records less than 10 Started Here
                    I_CUR_PAGE = 1
                    row_start = 2
                    row_end = tot_row + 1
                    for index in reversed(range(row_start,row_end)):
                        row_id = row_id + '/row['+str(int(index))+']' + ','
                        row_index.append(index)
                if not row_index and tot_row > 11: #This block is used to suppose user delete middle of page then we are redirect to previous page.
                    I_CUR_PAGE = I_CUR_PAGE - 1
                    row_range = self.ZeUI.getPaginationStartEndRecords(cur_page=I_CUR_PAGE)
                    row_start = tot_row - (row_range[1] - 1)
                    row_end = (tot_row - row_range[0] + 2)
                    for index in reversed(range(row_start,row_end)):
                        if index > 1:
                            row_id = row_id + '/row['+str(int(index))+']' + ','
                            row_index.append(index)
                result_set = self.getDecisionTableInfo(dec_table_idn=dec_table_idn,row_id=row_id[:-1],node_count=int(node_count))
                result_len = len(result_set)
                if not col_names:
                    col_names = self.getDecisionTableInfo(dec_table_idn=dec_table_idn,row_id='/row[1]',node_count=int(node_count)).tuples()[0]
                total_rec = tot_row-1
        header = self.ZeUI.getHeader()
        footer = self.ZeUI.getFooter()
        dtml_document = getattr(self.views, 'decision_table_result_page')
        if row_index:
            return dtml_document(self.views,
                                 REQUEST=request,
                                 col_names= col_names,
                                 total_rec=total_rec,
                                 I_CUR_PG=I_CUR_PAGE,
                                 result_len=result_len,
                                 dec_table_idn=dec_table_idn,
                                 row_index=row_index,
                                 result_set=result_set.tuples(),
                                 dec_table_name=dec_table_name,
                                 node_count=int(node_count),
                                 column_name=col_names,
                                 db_type=db_type,
                                 noResultMsg=noResultMsg)
        else:
            return dtml_document(self.views,
                                 REQUEST=request,
                                 total_rec=0,
                                 I_CUR_PG=I_CUR_PAGE,
                                 dec_table_idn=dec_table_idn,
                                 result_set='',
                                 dec_table_name=dec_table_name,
                                 node_count='',
                                 column_name='',
                                 db_type=db_type,
                                 noResultMsg=noResultMsg)

    def getDecisionTableInfo(self,dec_table_idn=None,row_id=None,db_type=False,row_start=0,row_end=0,order_by='',node_count=''):
        """
        return Decision Table Details
        """
        node_name,column_details = '',''
        if db_type: # ORACLE Related Changes
            val = 'replace(replace(extractValue(value(COL_VAL),'
            col = '/row/col'
            row_id = repr(row_id) # Because of Wrapper we had this change
            if not node_count:
                node_count = self.Sentinel.SentinelModel.selectDecisionTblColInfo(dec_table_idn=int(dec_table_idn),xml_path=repr('/table/row[1]'),row_block=repr('/row/*'))[0]['NUMBER_NODES']
            for i in range(node_count):
                node = col+str(i)
                node_name = node_name +'col'+str(i)+','
                gt_tag,lt_tag = '&gt;','&lt;'
                gt_symbol,lt_symbol = '>','<'
                column_details = column_details+val+' '+repr(node)+'),'+repr(gt_tag)+','+repr(gt_symbol)+'),'+repr(lt_tag)+','+repr(lt_symbol)+')'+' '+'col'+str(i)+','
        else: # MSSQL Related Changes
            datatype = 'varchar(max)'
            val = 'col.value('
            if not node_count:
                xml_path = "COUNT(DISTINCT 'col.value(''' + col.value('fn:local-name(.[1])', 'varchar(max)') + '[1]'', ''varchar(max)'') as '+ col.value('fn:local-name(.[1])', 'varchar(max)'))"
                node_count = self.Sentinel.SentinelModel.selectDecisionTblColInfo(dec_table_idn=int(dec_table_idn),xml_path=xml_path,row_block=repr('/row/*'))[0]['NUMBER_NODES']
            for i in range(node_count):
                node = 'col'+str(int(i))+'[1]'
                column_details = column_details+val+repr(node)+', '+repr(datatype)+') as col'+str(int(i)) + ','
            if not row_id: row_id = repr('/row') # Because of Wrapper we had this change
            else: row_id = repr(row_id)
        result_set = self.Sentinel.SentinelModel.selectDecisionTblInfo(dec_table_idn=int(dec_table_idn),column_details=column_details[:-1],row_id=row_id,db_type=db_type,row_start=row_start,row_end=row_end,node_name=node_name[:-1],order_by=order_by)
        return result_set

    def showEditDecisionTablePage(self):
        """
        @description : This method to show edit reference table page.
        @return : return to Edit Reference Page.
        """
        request = self.REQUEST
        row_index = int(request.get('row_index','0'))
        dec_table_id = int(request.get('dec_table_id','0'))
        cur_pag = int(request.get('cur_pag',1))
        db_type = self.ZeUtil.isOracle()
        if db_type:
            row_id = '/table/row['+str(row_index)+']'
            column_value = self.getDecisionTableInfo(dec_table_idn=dec_table_id,row_id=row_id,db_type=db_type,row_start=1,row_end=1,order_by='DESC').tuples()[0]
            col_names = self.getDecisionTableInfo(dec_table_idn=dec_table_id,row_id='/table/row[1]',db_type=db_type,row_start=1,row_end=1,order_by='DESC').tuples()[0]
        else:
            row_id = '/row['+str(1)+'],/row['+str(int(row_index))+']'
            result_set = self.getDecisionTableInfo(dec_table_idn=dec_table_id,row_id=row_id)
            col_names = result_set.tuples()[0]
            column_value = result_set.tuples()[1]
        header_type = ''
        if request.has_key('header_type'):
            header_type = request['header_type']
        header = self.ZeUI.getHeader(header_type)
        footer = self.ZeUI.getFooter(header_type)
        dtml_document = getattr(self.views,'edit_decision_table')
        return header+dtml_document(self.views, REQUEST=request,
                                    col_names=col_names,
                                    column_value=column_value,
                                    row_index=row_index,
                                    I_CUR_PG=cur_pag,
                                    dec_table_id=dec_table_id
                                    )+footer

    def updateDecisionRow(self):
        """
        @description : This method to update Decision row.
        @return : return either '0/1'
        """
        request = self.REQUEST
        user_idn = int(self.cms.ZeUser.Model.getLoggedinUserIdn())
        sequence_length = int(request.get('sequence_length',''))
        dec_table_id = int(request.get('dec_table_id','0'))
        row_index = int(request.get('row_index','0'))
        db_type = self.ZeUtil.isOracle()
        if db_type:
            for i in range(sequence_length):
                tdcolumnvalue = 'column_val'+str(int(i)+1)
                tdcolumnvalue = unquote(request.get(tdcolumnvalue,''))
                chars = []
                for char in tdcolumnvalue:
                    try:
                        chars.append(char.encode('ascii', 'strict'))
                    except UnicodeError:
                        chars.append('&#%i;' % ord(char))
                tdcolumnvalue = ''.join(chars)
                tdcolumnval = tdcolumnvalue.replace("&#","&amp;#").replace("<","&lt;").replace(">","&gt;").replace("'","''")
                add_node = '<col'+str(i)+'>'+tdcolumnval+'</col'+str(i)+'>'
                if len(add_node) <= 3986:
                    insert_stmt = repr('/table/row['+str(int(row_index))+']')+', '+repr('col'+str(i))+', XMLType('"'"+add_node+"'"')'
                    del_stmt = repr('/table/row['+str(int(row_index))+']/col'+str(i)+'[1]')
                    try:
                        self.Sentinel.SentinelModel.updateDecisioneRow(insert_stmt=insert_stmt,del_stmt=del_stmt,dec_table_id=dec_table_id,user_idn=user_idn)
                    except:
                        return 0
                else:
                    return 0
        else: # MSSQL changes
            for i in range(sequence_length):
                tdcolumnvalue = 'column_val'+str(int(i)+1)
                tdcolumnvalue = unquote(request.get(tdcolumnvalue,''))
                chars = []
                for char in tdcolumnvalue:
                    try:
                        chars.append(char.encode('ascii', 'strict'))
                    except UnicodeError:
                        chars.append('&#%i;' % ord(char))
                tdcolumnvalue = ''.join(chars)
                tdcolumnval = tdcolumnvalue.replace("&#","&amp;#").replace("<","&lt;").replace(">","&gt;").replace("'","''")
                add_node = '<col'+str(i)+'>'+tdcolumnval+'</col'+str(i)+'>'
                insert_stmt = "'"+'insert' +add_node+ ' as last into (row['+str(row_index)+'])'+"'"
                del_stmt = repr('delete (/row/col'+str(int(i))+')['+str(row_index)+']')
                try:
                    self.Sentinel.SentinelModel.\
                        updateDecisioneRow(\
                            insert_stmt = insert_stmt,
                            del_stmt = del_stmt,
                            dec_table_id = dec_table_id,
                            user_idn=user_idn
                        )
                except:
                    return 0
        Decisiontable.load(self, idn=dec_table_id).refresh_all_columnar_criteria()
        Decisiontable.load(self, idn=dec_table_id).refresh_all_columnar_actions()
        return 1

    def disableDecisionRow(self):
        """
        @description : This method to Disable the Reference Record
        @return : return 1.
        """
        request = self.REQUEST
        user_idn = int(self.cms.ZeUser.Model.getLoggedinUserIdn())
        i_dec_table_id = request.get('dec_table_id','')
        row_index = request.get('row_index',1)
        db_type = self.ZeUtil.isOracle()
        if db_type: 
            i_del_stmt = repr('/table/row['+str(row_index)+']')
        else: 
            i_del_stmt = repr('delete /row['+str(row_index)+']')
        self.Sentinel.SentinelModel.deActivateDecTableRow(\
                i_dec_table_id=i_dec_table_id,
                i_del_stmt=i_del_stmt,
                user_idn=user_idn
            )
        Decisiontable.load(self, idn=i_dec_table_id).refresh_all_columnar_criteria()
        Decisiontable.load(self, idn=i_dec_table_id).refresh_all_columnar_actions()
        return 1

    def showDecisionTableColumnDetails(self):
        """
        @description : This method to show column details for decision table.
        @return : return Filter Reference Page.
        """
        request = self.REQUEST
        dec_table_idn = request.get('dec_table_idn','')
        db_type = self.ZeUtil.isOracle()
        if db_type:
            col_names = self.getDecisionTableInfo(dec_table_idn=dec_table_idn,row_id='/table/row[1]',db_type=db_type,row_start=1,row_end=1,order_by='DESC').tuples()[0]
        else:
            col_names = self.getDecisionTableInfo(dec_table_idn=dec_table_idn,row_id='/row[1]').tuples()[0]
        current_page = 'add_decision_row'              
        dtml_document = getattr(self.views,current_page)
        return dtml_document(self.views, REQUEST=request,
                             col_names = col_names,
                             dec_table_idn=dec_table_idn
                             )
    
    def addNewDecisionTableRow(self):
        """
        @description : This method to add New Row in Decision table.
        @return : return to decision table result page.
        """
        request = self.REQUEST
        i_user_idn = int(self.cms.ZeUser.Model.getLoggedinUserIdn())
        sequence_length = int(request.get('sequence_length',''))
        i_dec_table_id = int(request.get('dec_table_idn','0'))
        db_type = self.ZeUtil.isOracle()
        if db_type:
            i_updt_stmt = '<row>'
            for i in range(sequence_length):
                i_updt_stmt += '<col'+str(i)+'>temp_data'+'</col'+str(i)+'>'
            i_updt_stmt += '</row>'
            self.Sentinel.SentinelModel.addNewDecisionTableRow(i_dec_table_id=i_dec_table_id,i_updt_stmt=repr(i_updt_stmt),i_user_idn=i_user_idn)
            tot_row = self.Sentinel.SentinelModel.selectDecisionTblColCount(dec_table_idn=int(i_dec_table_id),row_id=repr('/table/row'))[0]['TOT_ROW']
            for i in range(sequence_length):
                tdcolumnvalue = 'column_val'+str(int(i)+1)
                tdcolumnvalue = unquote(request.get(tdcolumnvalue,''))
                chars = []
                for char in tdcolumnvalue:
                    try:
                        chars.append(char.encode('ascii', 'strict'))
                    except UnicodeError:
                        chars.append('&#%i;' % ord(char))
                tdcolumnvalue = ''.join(chars)
                tdcolumnval = tdcolumnvalue.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace("'","''")
                add_node = '<col'+str(i)+'>'+tdcolumnval+'</col'+str(i)+'>'
                if len(tdcolumnval) <= 3986: # Column length should be less than 3986 character
                    insert_stmt = repr('/table/row['+str(int(tot_row))+']')+', '+repr('col'+str(i))+', XMLType('"'"+add_node+"'"')'
                    del_stmt = repr('/table/row['+str(int(tot_row))+']/col'+str(i)+'[1]')
                    try:
                        self.Sentinel.SentinelModel.updateDecisioneRow(insert_stmt=insert_stmt,del_stmt=del_stmt,dec_table_id=i_dec_table_id,user_idn=i_user_idn)
                    except:
                        return 0
                else:
                    return 0
        else:
            i_updt_stmt = 'insert <row> '
            for i in range(sequence_length):
                i_updt_stmt += '<col'+str(i)+'>temp_data'+'</col'+str(i)+'>'
            i_updt_stmt = i_updt_stmt +'</row> as last into (/)[1]'
            self.Sentinel.SentinelModel.addNewDecisionTableRow(i_dec_table_id=i_dec_table_id,i_updt_stmt=repr(i_updt_stmt),i_user_idn=i_user_idn)
            tot_row = self.Sentinel.SentinelModel.selectDecisionTblColCount(dec_table_idn=int(i_dec_table_id),row_id=repr('/row'))[0]['tot_row']
            for i in range(sequence_length):
                tdcolumnvalue = 'column_val'+str(int(i)+1)
                tdcolumnvalue = unquote(request.get(tdcolumnvalue,''))
                chars = []
                for char in tdcolumnvalue:
                    try:
                        chars.append(char.encode('ascii', 'strict'))
                    except UnicodeError:
                        chars.append('&#%i;' % ord(char))
                tdcolumnvalue = ''.join(chars)
                tdcolumnvalue = tdcolumnvalue.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace("'","''")
                add_node = '<col'+str(i)+'>'+tdcolumnvalue+'</col'+str(i)+'>'
                insert_stmt = "'"+'insert' +add_node+ ' as last into (row['+str(tot_row)+'])'+"'"
                del_stmt = repr('delete (/row/col'+str(int(i))+')['+str(tot_row)+']')
                try:
                    self.Sentinel.SentinelModel.\
                        updateDecisioneRow(\
                            insert_stmt = insert_stmt,
                            del_stmt = del_stmt,
                            dec_table_id = i_dec_table_id,
                            user_idn=i_user_idn
                            )
                except:
                    return 0
        Decisiontable.load(self, idn=i_dec_table_id).refresh_all_columnar_criteria()
        Decisiontable.load(self, idn=i_dec_table_id).refresh_all_columnar_actions()
        return self.getDecisionTableResultPage(dec_table_idn=i_dec_table_id)

    def getReferenceTableResultPage(self,
                                    ref_table_idn='',
                                    i_column_idn='',
                                    i_search_value='',
                                    add_ref_row=''):
        """
        @description : This method to get reference table result page.

        @param : ref_table_idn {int} reference table id
        @param : i_column_idn {int} reference table column id
        @param : i_search_value {string} search value
        @param : add_ref_row {string} add reference row (flag)
        @return : returns reference table result page
        """
        request = self.REQUEST
        export_flag = request.get('export_flag','N')
        if add_ref_row == '':
            ref_table_filter = request.get('ref_table_filter','')
            if ref_table_filter: #filter reference table
                i_column_idn = request.get('i_column_filter_idn','')
                i_search_value = request.get('i_search_filter_value','')
            else:
                if request.get('i_column_idn',''): #After Filter that mean pagination scenario
                    i_column_idn = request.get('i_column_idn','')
                    i_search_value = request.get('i_search_value','')
        total_count = self.Sentinel.SentinelModel.selectRefTableDetailCount(\
            ref_table_idn=ref_table_idn,
            i_column_idn=i_column_idn,
            i_search_value=i_search_value
            )[0][0]

        column_details=self.Sentinel.SentinelModel.getColumnValues(\
            ref_table_idn=ref_table_idn).dictionaries()
        no_of_column=column_details.__len__()
        i_query_limit = int(self.ZeUI.getDefRecPerPage())*no_of_column

        I_CUR_PAGE = int(request.get('I_CUR_PAGE','1'))
        if export_flag == 'Y': # Export Reference Table
            I_START_REC_NO = 1
            I_END_REC_NO = total_count*no_of_column
        else:
            if I_CUR_PAGE>1:
                I_START_REC_NO = (I_CUR_PAGE*i_query_limit)-\
                               i_query_limit
                I_START_REC_NO = I_START_REC_NO+1
                I_END_REC_NO = I_START_REC_NO + self.ZeUI.getDefRecPerPage()-1
                I_END_REC_NO = (I_END_REC_NO + i_query_limit)-\
                             self.ZeUI.getDefRecPerPage()
            else:
                I_START_REC_NO=0
                I_START_REC_NO = I_START_REC_NO+1
                I_END_REC_NO = I_START_REC_NO + self.ZeUI.getDefRecPerPage()-1
                I_END_REC_NO = (I_END_REC_NO * no_of_column)
        new_ref_list=self.Sentinel.SentinelModel.selectRefTableDetail(\
            ref_table_idn=ref_table_idn,
            query_from=I_START_REC_NO,
            query_to=I_END_REC_NO,
            i_column_idn=i_column_idn,
            i_search_value=i_search_value
            ).dictionaries()
        if I_CUR_PAGE > 1 and not new_ref_list:
            I_CUR_PAGE = I_CUR_PAGE - 1
            I_START_REC_NO = (I_CUR_PAGE*i_query_limit)-\
                               i_query_limit
            I_START_REC_NO = I_START_REC_NO+1
            I_END_REC_NO = I_START_REC_NO + self.ZeUI.getDefRecPerPage()-1
            I_END_REC_NO = (I_END_REC_NO * no_of_column)
            new_ref_list=self.Sentinel.SentinelModel.selectRefTableDetail(\
                ref_table_idn=ref_table_idn,
                query_from=I_START_REC_NO,
                query_to=I_END_REC_NO,
                i_column_idn=i_column_idn,
                i_search_value=i_search_value
                ).dictionaries()
        col_ref_list=[]
        col_id_list=[]
        new_result_list=[]
        for refloop in new_ref_list:
            if refloop['COLUMN_NAME'] not in col_ref_list:
                col_ref_list.append(refloop['COLUMN_NAME'])
                col_id_list.append(refloop['COLUMN_ID'])

        for colloop in col_ref_list:
            lst=[]
            lst = [i for i in new_ref_list if colloop==i['COLUMN_NAME']]
            new_result_list.append(lst)

        lenOfCols=len(col_ref_list)
        new_ref_list = map(lambda res: list(res), zip(*new_result_list))
        new_ref_list.reverse()
        ref_table_name = ''
        if new_ref_list:
            ref_table_name = new_ref_list[0][0]['TABLE_NAME']
        else:
            if column_details:
                query_result = self.Sentinel.SentinelModel.getRefTableNames().dictionaries() # We need to modify this Query 
                for rs in query_result:
                    if str(ref_table_idn) == str(rs['ID']):
                        ref_table_name = str(rs['TITLE'])
                for pos in range(column_details.__len__()):
                    if column_details[pos]['POSITION'] == pos + 1:
                        col_ref_list.append(column_details[pos]['COLUMN_NAME'])
                lenOfCols=len(col_ref_list)
        noResultMsg=self.ZeUtil.getJivaMsg(msg_code='627')
        if ref_table_idn:
            request.set('ref_table_idn',ref_table_idn)
        if not no_of_column:
            no_of_column = 1
        if export_flag == 'Y': # Export Reference Table
            # Response redirected to the location of excel file in the zodb_repository
            excel_object_url = reference_table_export(self, new_ref_list, col_ref_list, ref_table_name)
            return request.RESPONSE.redirect(excel_object_url)
        else:
            dtml_document = getattr(self.views, 'reftbl_result_page')
            return dtml_document(\
                self.views, REQUEST=request,
                new_ref_list=new_ref_list,
                col_ref_list=col_ref_list,
                column_details=column_details,
                col_id_list=col_id_list,
                lenOfCols=lenOfCols,
                total_rec=total_count/no_of_column,
                I_CUR_PG=I_CUR_PAGE,
                number_column=no_of_column,
                i_search_value=i_search_value,
                i_column_idn=i_column_idn,
                noResultMsg=noResultMsg,
                ref_table_name=ref_table_name
            )

    def showEditReferenceTablePage(self):
        """
        @description : This method to show edit reference table page.
        @return : return to Edit Reference Page.
        """
        request = self.REQUEST
        header = self.ZeUI.getHeader()
        footer = self.ZeUI.getFooter()
        row_id = request.get('row_id','')
        ref_table_id = request.get('ref_table_id','')
        cur_pag = request.get('cur_pag',1)
        row_details = self.Sentinel.SentinelModel.\
                    getReferenceTableRowDetails(\
                        row_id=row_id,
                        ref_table_id= ref_table_id).\
                    dictionaries()
        dtml_document = getattr(self.views,'edit_reference_table')
        return header+dtml_document(self.views, REQUEST=request,
                                    row_details = row_details,
                                    row_idn=row_id,
                                    I_CUR_PG=cur_pag,
                                    ref_table_idn=ref_table_id
                                    )+footer

    def showReferenceTableColumnDetails(self):
        """
        @description : This method to show column details for reference table.
        @return : return Filter Reference Page.
        """
        request = self.REQUEST
        ref_table_idn = request.get('ref_table_idn','')
        column_details=self.Sentinel.SentinelModel.getColumnValues(\
            ref_table_idn=ref_table_idn).dictionaries()

        current_page = {True: 'add_reference_row', False: 'reference_table_filter'}\
                     [request.get('add_row','N') == 'Y']
        dtml_document = getattr(self.views,current_page)
        return dtml_document(self.views, REQUEST=request,
                             column_details = column_details,
                             ref_table_idn=ref_table_idn
                             )

    def updateReferenceRow(self):
        """
        @description : This method to update reference row.
        @return : return either '0/1'
        """
        request = self.REQUEST
        sequence_length = int(request.get('sequence_length',''))
        for i in range(sequence_length):
            tdcolumnvalue = 'column_val'+str(int(i)+1)
            value_idn = 'value_idn'+str(int(i)+1)
            tdcolumnvalue = {True: request.get(tdcolumnvalue,''), False: 'No Value'}\
                          [request.get(tdcolumnvalue,'') != '']
            chars = []
            for char in unquote(tdcolumnvalue):
                try:
                    chars.append(char.encode('ascii', 'strict'))
                except UnicodeError:
                    chars.append('&#%i;' % ord(char))
            tdcolumnvalue = ''.join(chars)
            value_idn = request.get(value_idn,'')
            try:
                self.Sentinel.SentinelModel.\
                    updateReferenceRow(\
                        column_value = unquote(tdcolumnvalue).replace("&amp;","&"),
                        value_idn=value_idn
                    )
            except:
                return 0
        return 1

    def disableReferenceTable(self):
        """
        @description : This method to Disable the Reference Record
        @return : return 1.
        """
        request = self.REQUEST
        try:
            user_id = int(self.cms.ZeUser.Model.getLoggedinUserIdn())
        except:
            user_id = 3
        row_id = request.get('row_id','')
        ref_table_id = request.get('ref_table_id','')
        row_details = self.Sentinel.SentinelModel.\
                    getReferenceTableRowDetails(\
                        row_id=row_id,
                        ref_table_id= ref_table_id).\
                    dictionaries()
        sre_value_idn = ','.join([str(val['VALUE_IDN']) for val in row_details])
        if sre_value_idn:
            self.Sentinel.SentinelModel.\
                disableReferenceTable(\
                sre_ref_value_idn = sre_value_idn,
                user_id=user_id
            )
        return 1

    def addReferenceTable(self):
        """
        @description : This method to add reference table.
        @return : return to reference table result page.
        """
        request = self.REQUEST
        ref_table_id = request.get('ref_table_idn',0)
        try:
            user_id = int(self.cms.ZeUser.Model.getLoggedinUserIdn())
        except:
            user_id = 3
        row_id = self.Sentinel.SentinelModel.selectMaxRefRowIdForTable(\
            ref_table_id).dictionaries()
        if row_id[0]['MAX_ROW_ID'] != '':
            row_id = row_id[0]['MAX_ROW_ID']
            row_id+= 1
        else:
            row_id = 1
        sequence_length = int(request.get('sequence_length',''))
        for i in range(sequence_length):
            cell_value = 'column_val'+str(int(i)+1)
            col_id = 'column_idn'+str(int(i)+1)
            cell_value = {True: request.get(cell_value,''), False: 'No Value'}\
                       [request.get(cell_value,'') != '']
            chars = []
            for char in unquote(cell_value):
                try:
                    chars.append(char.encode('ascii', 'strict'))
                except UnicodeError:
                    chars.append('&#%i;' % ord(char))
            cell_value = ''.join(chars)
            col_id = request.get(col_id,'')
            try:
                self.Sentinel.SentinelModel.insertReferenceTableValue(\
                    ref_table_id,
                    int(col_id),
                    unquote(cell_value),
                    int(user_id),
                    row_id
                )
            except:
                return 0
        return self.getReferenceTableResultPage(ref_table_idn=ref_table_id,add_ref_row='Y')

    def showEventParamDetails(self):
        """
        @description : This method to show Event parameter detail
        @return : method to display parameter details for event
        """
        request = self.REQUEST
        first_name = request.get('i_first_name','')
        last_name = request.get('i_last_name','')
        enc_type_cd = request.get('enc_type_cd','')
        noResultMsg=self.ZeUtil.getJivaMsg(msg_code='627')

        header = self.ZeUI.getHeader()
        footer = self.ZeUI.getFooter()
        # pagination
        page_info = self.getPageDetails()
        rs = self.Sentinel.SentinelModel.\
           getClaimantEpisodeDetailsCount(\
               i_first_name=first_name,
               i_last_name=last_name,
               enc_type_cd=enc_type_cd
           )

        enc_details = self.Sentinel.SentinelModel.\
                    getClaimantEpisodeDetails(\
                        i_first_name=first_name,
                        i_last_name=last_name,
                        enc_type_cd=enc_type_cd,
                        i_start_rec_num=page_info['I_START_REC_NO'],
                        i_end_rec_num=page_info['I_END_REC_NO']
                    )
        dtml_document = getattr(self.views, 'event_parameter_detail')
        return header+dtml_document(self.views, REQUEST=self.REQUEST,
                                    enc_details=enc_details,
                                    i_first_name=first_name,
                                    i_last_name=last_name,
                                    enc_type_cd=enc_type_cd,
                                    total_rec=len(rs),
                                    I_CUR_PG=page_info['I_CUR_PAGE'],
                                    noResultMsg = noResultMsg)+footer

    def showEventParamPage(self):
        """
        @description : This method to show event parameter page.
        @return: Return Search Event Parameter Page.
        """
        request = self.REQUEST
        header = self.ZeUI.getHeader()
        footer = self.ZeUI.getFooter()
        dtml_document = getattr(self.views, 'event_parameter_search')
        return header+dtml_document(self.views,
                                    REQUEST=request
                                    )+footer

   
    def showEventAddPage(self):
        """
        @description : This method to show event add page.
        @return : returns Event Add page
        """
        request = self.REQUEST
        header_type = ''
        if request.has_key('header_type'):
            header_type = request['header_type']
        header = self.ZeUI.getHeader(header_type)
        footer = self.ZeUI.getFooter(header_type)
        I_CONTEXT_ID = request.get('I_CONTEXT_ID','')
        dtml_document = getattr(self.views, 'event_add')
        next_page = header+dtml_document(self.views,
                                         REQUEST=request,
                                         I_CONTEXT_ID=I_CONTEXT_ID
                                         )+footer
        return next_page

    def getClaimantEpisode(self):
        """
        @description : This method used to get claimant episode details.
        @ return : returns episode and claimant details
        """
        request = self.REQUEST
        paramset = request.get('paramset','')
        ret_msg = ''
        if paramset:
            sparams = paramset.split('@@')
            ret_msg='MBR_IDN='+str(sparams[0])
            ret_msg+='@@ENC_TYPE='+str(sparams[2])
            ret_msg+='@@ENC_IDN='+str(sparams[3])
            ret_msg+='@@USER_IDN='+str(sparams[1])
        return ret_msg

    @normalize_form()     
    def addEvent(self,fromInstaller=''):
        """
        @description : This method to add event.
        @return : returns Event Page
        """
        request=self.REQUEST
        try:
            user_id = int(self.cms.ZeUser.Model.getLoggedinUserIdn())
        except:
            user_id = 3
        event_title = request.get('event_title','')
        event_cd = event_title.split('@')[0]
        parameter_entity_active = 'Y'
        message = self.ZeUtil.getJivaMsg(msg_code = '438')
        I_CONTEXT_ID = request.get('I_CONTEXT_ID','')
        #new_parameter_string = request.get('event_pnames_values','')
        #processed_parameters = self.getParameterList(new_parameter_string)
        mbr_idn = request.get('I_CLAIMANT_IDN', None)
        enc_idn = request.get('I_ENCOUNTER_IDN', None)
        new_event_status = SE_EVENT_STATE_OPEN
        try:
            new_event_id_recordset = self.Sentinel.SentinelModel.\
                                   insertEvent(\
                                       event_status=new_event_status,
                                       user_id=user_id,
                                       event_cd=event_cd,
                                       mbr_idn=mbr_idn,
                                       enc_idn=enc_idn
                                   )

            new_event_id = new_event_id_recordset.\
                         dictionaries()[0]['SRE_EVENT_IDN']
            return '%s@@%s' %(new_event_id, new_event_status)
        except Exception,e:
            print "Error:",e

    def showEventEditPage(self):
        """
        @description : This method to show event edit page.
        @return: return Event Edit Page
        """
        request = self.REQUEST
        event_id = request.get('event_id','')
        event_title = request.get('event_title','')
        event_status = request.get('event_status','')
        I_CONTEXT_ID = request.get('I_CONTEXT_ID','')
        src = request.get('src','')
        msg_code = {'addEvent':'438','updateEvent':'439'}
        if src:
            request.set('info_alert', self.ZeUtil.getJivaMsg(msg_code = msg_code[src]))
        header = self.ZeUI.getHeader()
        footer = self.ZeUI.getFooter()
        dtml_document = getattr(self.views, 'event_edit')
        next_page = header+dtml_document(self.views,
                                         REQUEST=request,
                                         I_CONTEXT_ID=I_CONTEXT_ID,
                                         event_title=event_title,
                                         event_status=event_status,
                                         event_id=event_id
                                         )+footer
        return next_page

    @normalize_form()     
    def updateEvent(self):
        """
        @description : This method to update event.
        @return : return event edit page.
        """
        request = self.REQUEST
        try:
            user_id = int(self.cms.ZeUser.Model.getLoggedinUserIdn())
        except:
            user_id = 3

        #I_CONTEXT_ID = request.get('I_CONTEXT_ID','')
        #event_parameter_value = request.get('event_pnames_values_'+I_CONTEXT_ID,'')
        event_status = request.get('event_status','')
        event_id = request.get('eventID',0)
        if event_status == '':
            event_status = SE_EVENT_STATE_OPEN
        #processed_parameters = self.getParameterList(event_parameter_value)
        try:
            event_id_recordset = self.Sentinel.SentinelModel.updateEvent(\
                event_status=event_status,
                user_id=user_id,
                event_id=event_id
            )
        except:
            return 0
        request.set('src','updateEvent')
        return self.showEventEditPage()


    def getParameterList(self,parameter_string):
        """
        @description : This method to get event parameter list.
        @param : parameter_string {string} parameter
        @return:return Parameter List
        """
        processed_parameters = []
        striped_parameter_string = parameter_string.strip()
        if striped_parameter_string:
            raw_parameter_list = [each.strip()\
                                  for each in striped_parameter_string.split('\n')]
            for eachRawParameter in raw_parameter_list:
                eachRawParameterList = eachRawParameter.split('=')
                if len(eachRawParameterList) == 2:
                    processed_parameters.append(\
                        (
                            eachRawParameterList[0].strip(),
                            eachRawParameterList[1]
                        )
                    )
        return processed_parameters

    def getEventParameterDetails(self):
        """
        @description : This method to get event parameter detail

        @param : eventID {int} event id.
        @return : returns event parameter string for given event id
        """
        request = self.REQUEST
        eventID = request.get('event_id', '')
        header = self.ZeUI.getHeader()
        footer = self.ZeUI.getFooter()
        event_parameter = self.Sentinel.SentinelModel.\
                            selectEventParameterDetails(\
                                event_id=eventID)
        if event_parameter.dictionaries()[0]['EVENT_PARAMS'] != '':
            event_parameter_list = eval(event_parameter.dictionaries()[0]['EVENT_PARAMS'])
        else:
            event_parameter_list = ''
        noResultMsg=self.ZeUtil.getJivaMsg(msg_code='627')
        dtml_document = getattr(self.views, 'event_params_result_page')
        return header+dtml_document(\
            self.views,
            REQUEST=request,
            event_parameter_list=event_parameter_list,
            noResultMsg=noResultMsg
            )+footer

    def showEventPage(self):
        """
        @description : This method to show event search page.
        @return : returns Event page
        """
        request = self.REQUEST
        header_type = ''
        if request.has_key('header_type'):
            header_type = request['header_type']
        header = self.ZeUI.getHeader(header_type)
        footer = self.ZeUI.getFooter(header_type)
        I_CONTEXT_ID = request.get('I_CONTEXT_ID','')
        dtml_document = getattr(self.views, 'event_search')
        next_page = header+dtml_document(self.views, 
                                         REQUEST=request,
                                         I_CONTEXT_ID=I_CONTEXT_ID
                                         )+footer
        return next_page

    def getEventsResultPage(self):
        """
        @description : This method to get event result page.
        @return : returns Event Result page
        """
        request = self.REQUEST
        event_name_id = request.get('event_title','')
        event_status = request.get('event_status','')
        I_CONTEXT_ID = request.get('I_CONTEXT_ID','')
        # Left Navigation Event Status
        if event_status == 'All':
            event_status = ''

        header = self.ZeUI.getHeader()
        footer = self.ZeUI.getFooter()
        # pagination
        page_info = self.getPageDetails()

        next_count = self.Sentinel.SentinelModel.selectEventDetailsCount(\
            event_name_id=event_name_id,
            event_status=event_status
            )[0][0]

        new_event_recordset = self.Sentinel.SentinelModel.\
                            selectEventDetails(\
                                event_name_id=event_name_id,
                                event_status=event_status,
                                query_from=page_info['I_START_REC_NO'],
                                query_to=page_info['I_END_REC_NO']
                            )

        new_event_list = new_event_recordset.dictionaries()
        noResultMsg=self.ZeUtil.getJivaMsg(msg_code='627')
        dtml_document = getattr(self.views, 'event_result_page')
        return header+dtml_document(\
            self.views,
            REQUEST=request,
            new_event_list=new_event_list,
            total_rec=next_count,
            I_CUR_PG=page_info['I_CUR_PAGE'],
            i_event_title=event_name_id,
            i_event_status=event_status,
            noResultMsg=noResultMsg
            )+footer

    def showCriteriaPage(self):
        """
        @description : This method to show criteria search page.
        @return : return to criteria search page
        """
        request = self.REQUEST
        criteriatype = self.getCriteriaType()
        ruletype = constants.RULE_TYPE
        header_type = ''
        if request.has_key('header_type'):
            header_type = request['header_type']
        header = self.ZeUI.getHeader(header_type)
        footer = self.ZeUI.getFooter(header_type)
        I_CONTEXT_ID = request.get('I_CONTEXT_ID','')
        dtml_document = getattr(self.views, 'criteria_search')
        next_page = header+dtml_document(self.views, 
                                         request=request,
                                         I_CONTEXT_ID=I_CONTEXT_ID,
                                         criteriatype=criteriatype,
                                        ruletype=ruletype
                                         )+footer
        return next_page

    def getCriteriaResultPage(self):
        """
        @description : This method to get criteria result page.
        @return : return criteria result page,
        """
        request = self.REQUEST
        criteria_name    = self.ZeUtil.replaceQuotes(request.get('criteria_title','').strip())
        criteria_id      = request.get('criteria_id','')
        entity           = request.get('entity','').strip()
        entity_attribute = request.get('entity_attribute','').strip()
        criteria_reftable = request.get('criteria_reftable',0)
        rule_enabled = request.get('filter_enabled','Y')
        dec_table_id = request.get('dec_table_id', '')
        rule_type = request.get('Rule type', '')
        criteria_type = request.get('criteria_type', '')
        noResultMsg=self.ZeUtil.getJivaMsg(msg_code='627')
        # pagination
        page_info = self.getPageDetails()
        rule_enabled = request.get('filter_enabled','Y')
        next_count = self.Sentinel.SentinelModel.selectCriteriaDetailsCount(criteria_id=criteria_id,
                                                                            criteria_name=criteria_name,
                                                                            entity = entity,
                                                                            dec_table_id=dec_table_id,
                                                                            rule_enabled = rule_enabled,
                                                                            rule_type = rule_type,
                                                                            criteria_type = criteria_type,
                                                                            criteria_reftable = criteria_reftable,
                                                                            entity_attribute = entity_attribute)[0][0]
        new_criteria_recordset = self.Sentinel.SentinelModel.selectCriteriaDetails(criteria_id=criteria_id,
                                                                                   criteria_name=criteria_name,
                                                                                   dec_table_id=dec_table_id,
                                                                                   entity = entity,
                                                                                   rule_enabled=rule_enabled,
                                                                                   rule_type = rule_type,
                                                                                   criteria_type = criteria_type,
                                                                                   entity_attribute = entity_attribute,
                                                                                   criteria_reftable = criteria_reftable,
                                                                                   query_from=page_info['I_START_REC_NO'],
                                                                                   query_to=page_info['I_END_REC_NO'])

        new_criteria_list = new_criteria_recordset.dictionaries()
        noResultMsg=self.ZeUtil.getJivaMsg(msg_code='627')
        dtml_document = getattr(self.views,'criteria_result_page')
        return dtml_document(\
            self.views,
            REQUEST=request,
            new_criteria_list=new_criteria_list,
            criteria_id = criteria_id,
            total_rec=next_count,
            filter_enabled=rule_enabled,
            I_CUR_PG=page_info['I_CUR_PAGE'],
            criteria_title=criteria_name,
            entity=entity,
            entity_attribute=entity_attribute,
            criteria_reftable=criteria_reftable,
            noResultMsg=noResultMsg,
            rule_type = rule_type,
            criteria_type = criteria_type,
            dec_table_id=dec_table_id
        )

    def getValidAttributeOperators(self):
        """
        @description : This method to get valid attribute operators.
        @return : returns dictionary of valid attribute operators
        """
        return constants.VALID_ATTRIBUTE_OPERATORS_DICT

    def getCriteriaType(self):
        """
        @description : This method to get criteria type
        @return : return criteria type
        """
        return constants.CRITERIA_TYPE

    def showCriteriaResultFields(self):
        """
        """
        request = self.REQUEST
        I_CONTEXT_ID = request.get('I_CONTEXT_ID','')
        criteria_type = request.get('criteria_type', '')
        if criteria_type == 'TEST_AGAINST_VALUE':
            operators = constants.TEST_AGAINST_VALUE
            dtml_document = getattr(self.views, 'compare_with_value_criteria_page')
        elif criteria_type == 'TEST_AS_BOOLEAN':
            operators = constants.TEST_AS_BOOLEAN
            dtml_document = getattr(self.views, 'true_false_criteria_page')
        elif criteria_type == 'DATE/TIME COMPARISON':
            operators = constants.DATE_TIME_COMPARISON
            dtml_document = getattr(self.views, 'date_time_comparison_criteria_page')
        elif criteria_type == 'EXISTS_IN_REFTABLE':
            operators = constants.EXISTS_IN_REFTABLE
            dtml_document = getattr(self.views, 'look_up_reference_table_criteria_page')
        elif criteria_type == 'TEST_AGAINST_COLUMN':
            operators = constants.DECISION_TABLE_OPERATORS_DICT
            dtml_document = getattr(self.views, 'decision_table_criteria_page')
        else:
            return False
        return dtml_document(self.views,\
                             REQUEST = request,
                             I_CONTEXT_ID = I_CONTEXT_ID,
                             operators = operators)

    def addDecisionTblCondition(self):
        """
        @description : This method to get decision table condition
        """
        request = self.REQUEST
        I_CONTEXT_ID = request.get('I_CONTEXT_ID','')
        operators = constants.DECISION_TABLE_OPERATORS_DICT
        dtml_document = getattr(self.views, 'decision_table_criteria_conditions')
        return dtml_document(self.views,\
                             REQUEST = request,
                             I_CONTEXT_ID = I_CONTEXT_ID,
                             operators = operators)

    def showCriteriaAddPage(self):
        """
        @description : This method to show criteria add page
        @return: returns to criteria add page
        """
        request = self.REQUEST
        criteriatype = self.getCriteriaType()
        ruletype = constants.RULE_TYPE
        header = self.ZeUI.getHeader()
        footer = self.ZeUI.getFooter()
        dtml_document = getattr(self.views, 'criteria_add')
        return header+dtml_document(self.views,\
                                    REQUEST = request,
                                    criteriatype=criteriatype,
                                    ruletype=ruletype
                                    )+footer

    def getColumnIdsforTable(self,ref_table_idn='',template_call='N'):
        """
        @description : This method to get column id for reference table.
        @return : return column list.
        """
        request = self.REQUEST
        if not ref_table_idn:
            ref_table_idn = request.get('ref_table_idn','')

        if ref_table_idn:
            col_list=self.Sentinel.SentinelModel.getColumnValues(\
                ref_table_idn=ref_table_idn
                ).dictionaries()
            if template_call == 'N':
                result_set='<select align="left"\
                                name="refcolumn" class="mandatorychk">\
                                <option value="">---Select One---</option>'
                for rs in col_list:
                    result_set+="<option value="+str(rs['COLUMN_ID'])+">"\
                              +str(rs['COLUMN_NAME'])+"</option>"
                result_set+='</select>'
                return result_set
            else:
                return col_list
        else:
            result_set='<select align="left"\
                                name="refcolumn" class="mandatorychk">\
                                <option value="">---Select One---</option>'
            if template_call == 'N':
                return result_set
            else:
                return ''

    def getCriteriaEntityValues(self,entity_name,rule_type,template_call = 'N'):
        """
        @description : Method to get entity attributes for a given entity name
        @param : entity name {string}
        @param : template call - default - 'N' a js call
        @return : construct a html query if a call is not from template,
                  if a call is from template return a dictionary object

        """
        request = self.REQUEST
        criteria_type = request.get('criteria_type', '')
        result_set = self.Sentinel.SentinelModel.getCriteriaEntityValues(criteria_type, rule_type, entity_name=entity_name).dictionaries()
        I_CONTEXT_ID = request.get('I_CONTEXT_ID', '')
        formName = request.get('formName','')        
        if template_call == 'N':
            if formName and formName.startswith('add'):
                sel_attr='<select name="entity_attribute" class="mandatorychk" onChange="$SENTINEL.getCustomCriteriaFields(\'addCriteria_'+I_CONTEXT_ID+'\', \'customCritFields_'+I_CONTEXT_ID+'\')">'
            elif formName and formName.startswith('update'):
                sel_attr='<select name="entity_attribute" class="mandatorychk" onChange="$SENTINEL.getCustomCriteriaFields(\'updatecriteria_'+I_CONTEXT_ID+'\', \'customCritFields_'+I_CONTEXT_ID+'\')">'
            else:
                sel_attr='<select name="entity_attribute" class="mandatorychk">'
            sel_attr+='<option value="">---Select One---</option>'
            if entity_name:
                for res_value in result_set:
                    sel_attr+='<option value='+str(res_value['ENTITY_ID'])+'>'+\
                            str(res_value['ATTR_TITLE'])+'</option>'
            sel_attr+='</select>'
            return sel_attr
        else:
            return result_set

    def getCriteriaEntityValuesForDecTable(self,entity_name,template_call = 'N'):
        """
        @description : Method to get entity attributes for a given entity name
        @param : entity name {string}
        @param : template call - default - 'N' a js call
        @return : construct a html query if a call is not from template,
                  if a call is from template return a dictionary object

        """
        request = self.REQUEST
        result_set = self.Sentinel.SentinelModel.getCriteriaEntityValuesForDecTable(entity_name=entity_name).dictionaries()
        I_CONTEXT_ID = request.get('I_CONTEXT_ID', '')
        formName = request.get('formName','')        
        row_id = request.get('rowid', '')
        if template_call == 'N':
            sel_attr='<select name="entity_attribute_r'+row_id+'" class="mandatorychk">'
            sel_attr+='<option value="">---Select One---</option>'
            if entity_name:
                for res_value in result_set:
                    sel_attr+='<option value='+str(res_value['ENTITY_ID'])+'>'+\
                            str(res_value['ATTR_TITLE'])+'</option>'
            sel_attr+='</select>'
            return sel_attr
        else:
            return result_set

    @normalize_form(('criteria_operator'))
    def addCriteria(self):
        """
        @description : This method is used to Add new criteria
        @return : return criteria edit page.
        """
        request = self.REQUEST
        try:
            user_id = int(self.cms.ZeUser.Model.getLoggedinUserIdn())
        except:
            user_id = 3
        I_CONTEXT_ID = request.get('I_CONTEXT_ID','')
        criteria_title = request.get('criteria_title','').strip()
        new_operator = request.get('criteria_operator','')
        operators = constants.VALID_ATTRIBUTE_OPERATORS_DICT
        if new_operator:
            new_operator = operators[new_operator]
        criteria_value = request.get('criteria_value','').strip()
        entity = request.get('entity','')
        criteria_type = request.get('criteria_type')
        entity_column = request.get('entity_attribute','')
        source = request.get('source','')
        referencetable_idn = request.get('reftbl','')
        referencecolumn_idn = request.get('refcolumn','')
        new_description = request.get('criteria_description','').strip()
        dec_table_id = ''
        additional_values = ''
        condition_criteria = 0
        if criteria_type == 'CUSTOM':
            customFieldLength = int(request.get('customFieldLength', ''))
            if customFieldLength:
                additional_values = {}
                #val_lst = ['','']
                for i in range(customFieldLength):
                    cust_value = request['x'+str(i+1)].strip()
                    if re.findall("'",cust_value):
                        additional_values['x'+str(i+1)] = cust_value
                    if not cust_value.startswith("'") and\
                       (not (cust_value.startswith("(") and cust_value.endswith(")")))\
                       and (not re.match("^[0-9]*$", cust_value)):
                        cust_value = "'"+cust_value+"'"
                    additional_values['x'+str(i+1)] = ast.literal_eval(cust_value)
        if new_operator=='no operator':
            referencecolumn_idn = ''
            referencetable_idn = ''
            criteria_value = ''
            condition_criteria = 0
            new_operator = {True: '', False: new_operator}[criteria_type == 'CUSTOM']
        if criteria_type=='EXISTS_IN_REFTABLE':
            criteria_value = ''
            condition_criteria = 1
        if source=='source_static':
            referencecolumn_idn = ''
            referencetable_idn = ''
            condition_criteria = 0

        # Following inputs are being used for date time criteria
        from_dt = ''
        to_dt = ''

        if source=='source_absolute_datetime':
            referencecolumn_idn = ''
            referencetable_idn = ''
            criteria_value = ''
            condition_criteria = 0

            absolute_from_date = request.get('absolute_from_date','')
            absolute_from_hrs = request.get('absolute_from_hrs','')
            absolute_from_min = request.get('absolute_from_min','')
            absolute_from_ampm = request.get('absolute_from_ampm','')

            absolute_to_date = request.get('absolute_to_date','')
            absolute_to_hrs = request.get('absolute_to_hrs','')
            absolute_to_min = request.get('absolute_to_min','')
            absolute_to_ampm = request.get('absolute_to_ampm','')

            if absolute_from_date and absolute_from_hrs and absolute_from_min:
                from_dt_str = "%s %s:%s:00 %s" % (absolute_from_date,
                                                  absolute_from_hrs,
                                                  absolute_from_min,
                                                  absolute_from_ampm)
                #parse time using 12 hour clock
                parsed_from_dt = datetime.strptime(from_dt_str,
                                                   "%m/%d/%Y %I:%M:%S %p")
                from_dt = parsed_from_dt.strftime("%m/%d/%Y %H:%M:%S")

            if absolute_to_date and absolute_to_hrs and absolute_to_min:
                to_dt_str = "%s %s:%s:00 %s" % (absolute_to_date,
                                                absolute_to_hrs,
                                                absolute_to_min,
                                                absolute_to_ampm)
                #parse time using 12 hour clock
                parsed_to_dt = datetime.strptime(to_dt_str,
                                                 "%m/%d/%Y %I:%M:%S %p")
                to_dt = parsed_to_dt.strftime("%m/%d/%Y %H:%M:%S")

        if source == 'source_relative_datetime':
            referencecolumn_idn = ''
            referencetable_idn = ''
            criteria_value = ''
            condition_criteria = 0

            lookback_period = request.get('lookback_period','')
            relative_type = request.get('relative_type','')

            relative_date = request.get('relative_date','')
            relative_hrs = request.get('relative_hrs','')
            relative_min = request.get('relative_min','')
            relative_ampm = request.get('relative_ampm','')

            if (relative_type and lookback_period):
                if (relative_date and relative_hrs and relative_min):

                    to_dt_str = "%s %s:%s:00 %s" % (relative_date,
                                                    relative_hrs,
                                                    relative_min,
                                                    relative_ampm)
                    # parse the to_dt string using 12 hour clock
                    new_from_dt = datetime.strptime(to_dt_str, "%m/%d/%Y %I:%M:%S %p")
                    to_dt = new_from_dt.strftime("%m/%d/%Y %H:%M:%S")

                    if relative_type in constants.unit_limits:
                        from_dt = new_from_dt - timedelta(hours=int(constants.unit_limits[relative_type])*int(lookback_period))
                    if relative_type == 'Month(s)':
                        mx_new_from_dt = mx_date_time(new_from_dt.year,
                                                      new_from_dt.month,
                                                      new_from_dt.day,
                                                      new_from_dt.hour,
                                                      new_from_dt.minute,
                                                      new_from_dt.second)
                        from_dt =  mx_new_from_dt - RelativeDateTime(months=int(lookback_period))

                    if relative_type == 'Year(s)':
                        mx_new_from_dt = mx_date_time(new_from_dt.year,
                                                      new_from_dt.month,
                                                      new_from_dt.day,
                                                      new_from_dt.hour,
                                                      new_from_dt.minute,
                                                      new_from_dt.second)
                        from_dt = mx_new_from_dt - RelativeDateTime(years=int(lookback_period))

                    from_dt = from_dt.strftime("%m/%d/%Y %H:%M:%S")

                criteria_value = str(lookback_period)+'@@'+str(relative_type)

                dec_table_id = ''
        if criteria_type == 'TEST_AGAINST_COLUMN':
            conditionCount = request.get('conditionCount', '')
            dec_table_id = request.get('dec_table_id' , '')
            criteria_id = []
            dec_tble_operators = constants.DECISION_TABLE_OPERATORS_DICT
            col_details = self.getDecTableColumns(dec_table_id=dec_table_id,template_call = 'Y')
            for i in range(0, int(conditionCount)):
                dec_column_num = request.get('dec_column_name_r'+str(i+1), '')
                ext_criteria_cd = "CRITERIA"+get_base_external_cd(self)
                if dec_column_num:
                    entity_column = request.get('entity_attribute_r'+str(i+1), '')
                    entity_attr_details = self.Sentinel.SentinelModel.getCriteriaEntityValuesForDecTable(entity_idn=entity_column).dictionaries()
                    new_operator = request.get('criteria_operator_r'+str(i+1), '')
                    if new_operator:
                        new_operator = dec_tble_operators[new_operator]
                    mod_criteria_title = criteria_title+'_'+col_details[dec_column_num]+'_op( '+new_operator+' )'
                    criteriaId = Decisiontable.load(self, idn=dec_table_id).create_columnar_criterion(title=mod_criteria_title,
                                                                                                      entity_name = entity_attr_details[0]['NAME'],
                                                                                                      entity_attr = entity_attr_details[0]['ENTITY_ATTR'],
                                                                                                      binary_op = new_operator,
                                                                                                      tbl_colno = int(dec_column_num),
                                                                                                      ext_criteria_cd = ext_criteria_cd)


                #criteria_id.append(criteriaId[0]['SRE_CRITERIA_IDN'])
            return dec_table_id
        ext_criteria_cd = "CRITERIA"+get_base_external_cd(self)
        criteriaId = self.Sentinel.SentinelModel.insertCriteria(criteria_title=criteria_title,
                                                                criteria_value=criteria_value,
                                                                criteria_type=criteria_type,
                                                                operator=new_operator,
                                                                description=new_description,
                                                                ref_column_idn=referencecolumn_idn,
                                                                ref_tbl_idn=referencetable_idn,
                                                                entity_column=entity_column,
                                                                user_id=user_id,
                                                                from_date=from_dt,
                                                                to_date=to_dt,
                                                                additional_values=additional_values,
                                                                dec_table_id = dec_table_id,
                                                                ext_criteria_cd = ext_criteria_cd)
        criteria_id = criteriaId[0]['SRE_CRITERIA_IDN']
        # Additional conditions used for reference table
        if condition_criteria:
            self.addCriteriaAdditionalCondition(criteria_id=criteria_id,user_id=user_id)
        return criteria_id

    def showCriteriaEditPage(self):
        """
        @description : This method is used to show criteria edit page.
        @return : return criteria edit page.
        """
        request = self.REQUEST
        criteria_id = request.get('criteria_id','')
        additional_criteria = self.getCriteriaCondResults(criteria_id)
        additional_criteria = additional_criteria.__len__()
        criteria_type = request.get('criteria_type', '')
        criteria_title = request.get('criteria_title', '')
        criteriatype = self.getCriteriaType() 
        if criteria_type == 'TEST_AGAINST_VALUE':
            operators = constants.TEST_AGAINST_VALUE
            ResultFields = self.views.compare_with_value_criteria_edit_page
            Custom_ResultFields = ''
        elif criteria_type == 'TEST_AS_BOOLEAN':
            operators = constants.TEST_AS_BOOLEAN
            ResultFields = self.views.true_false_criteria_page
            Custom_ResultFields = ''
        elif criteria_type == 'DATE/TIME COMPARISON':
            operators = constants.DATE_TIME_COMPARISON
            ResultFields = self.views.date_time_comparison_criteria_edit_page
            Custom_ResultFields = ''
        elif criteria_type == 'EXISTS_IN_REFTABLE':
            operators = constants.EXISTS_IN_REFTABLE
            ResultFields = self.views.look_up_reference_table_criteria_edit_page
            Custom_ResultFields = ''
        elif criteria_type == 'CUSTOM':
            operators = {}
            ResultFields = ''
            Custom_ResultFields = self.views.custom_criteria_edit_page
        I_CONTEXT_ID = request.get('I_CONTEXT_ID','')
        src = request.get('src','')
        msg_code = {'addCriteria':'440','updateCriteria':'441'}
        if src:
            request.set('info_alert', self.ZeUtil.getJivaMsg(msg_code = msg_code[src]))
        if request.get('reset',''):
            request.set('info_alert', '')
        header = self.ZeUI.getHeader()
        footer = self.ZeUI.getFooter()
        dec_table_id = request.get('dec_table_id','')
        if (criteria_type == 'TEST_AGAINST_COLUMN' or dec_table_id):
            dec_tble_operators = constants.DECISION_TABLE_OPERATORS_DICT
            total_dec_crit_records =  self.Sentinel.SentinelModel.getTotalDecCriteriaRecords(dec_table_id=int(dec_table_id))
            clauses_records = self.Sentinel.SentinelModel.selectCriteriaDetails(dec_table_id=dec_table_id,
                                                                                query_from=1,
                                                                                query_to=total_dec_crit_records[0]['TOTAL_RECORDS']).dictionaries()
            conditionCount = len(clauses_records)
            criteria_description = clauses_records[0]['DESCRIPTION']
            decColDetails = self.getDecTableColumns(dec_table_id=dec_table_id, template_call = 'Y')
            criteria_title = clauses_records[0]['TITLE'].split('_')[0]
            dtml_document = getattr(self.views, 'dec_table_criteria_edit_page')
            next_page = header+dtml_document(self.views,
                                             REQUEST = request,
                                             dec_table_id=dec_table_id,
                                             criteriatype=criteriatype,
                                             dec_crit_records=len(clauses_records),
                                             clauses_records=clauses_records,
                                             operators=dec_tble_operators,
                                             criteria_title=criteria_title,
                                             decColDetails=decColDetails,
                                             criteria_description=criteria_description,
                                             I_CONTEXT_ID=I_CONTEXT_ID,
                                             criteria_type=criteria_type,
                                             conditionCount=conditionCount
                                             )+footer
        else:
            clauses_records = self.Sentinel.SentinelModel.selectCriteriaDetails(criteria_id=criteria_id,
                                                                                query_from=1,
                                                                                query_to=1).dictionaries()

            #operators = self.getValidAttributeOperators()
            criteriatype = self.getCriteriaType()
            additional_value = dict()
            if (clauses_records[0]['ADDITIONAL_VALUES']):
                additional_value = eval(clauses_records[0]['ADDITIONAL_VALUES'])
            entity_attr_idn = clauses_records[0]['SRE_ENTITY_IDN1']
            ident_custom_pattern = EntityAttr.load(self, idn=entity_attr_idn).populate_additional_values()
            customFieldLength = len(ident_custom_pattern)
            label={}
            custom_default_fields = {}
            for i in range(len(ident_custom_pattern)):
                label[ident_custom_pattern[i].split(':')[0][3:-1]] = ident_custom_pattern[i].split(':')[2][1:-3]
                custom_default_fields[ident_custom_pattern[i].split(':')[0][3:-1]] = ident_custom_pattern[i].split(':')[1]
            dtml_document = getattr(self.views, 'criteria_edit')
            next_page = header+dtml_document(self.views,
                                             REQUEST = request,
                                             criteria_id=criteria_id,
                                             clauses_records=clauses_records,
                                             I_CONTEXT_ID=I_CONTEXT_ID,
                                             operators=operators,
                                             criteriatype=criteriatype,
                                             additional_criteria=additional_criteria,
                                             label=label,
                                             customFieldLength=customFieldLength,
                                             additional_value=additional_value,
                                             custom_default_fields=custom_default_fields,
                                             Custom_ResultFields=Custom_ResultFields,
                                             ResultFields=ResultFields)+footer
        return next_page

    def showCriteriaViewPage(self):
        """
        @description : This method is used to show criteria edit page.
        @return : return criteria edit page.
        """
        request = self.REQUEST
        criteria_id = request.get('criteria_id','')
        additional_criteria = self.getCriteriaCondResults(criteria_id)
        additional_criteria = additional_criteria.__len__()
        criteria_type = request.get('criteria_type', '')
        criteria_title = request.get('criteria_title', '')
        criteriatype = self.getCriteriaType() 
        if criteria_type == 'TEST_AGAINST_VALUE':
            operators = constants.TEST_AGAINST_VALUE
            ResultFields = self.views.compare_with_value_criteria_view_page
            Custom_ResultFields = ''
        elif criteria_type == 'TEST_AS_BOOLEAN':
            operators = constants.TEST_AS_BOOLEAN
            ResultFields = self.views.true_false_criteria_page
            Custom_ResultFields = ''
        elif criteria_type == 'DATE/TIME COMPARISON':
            operators = constants.DATE_TIME_COMPARISON
            ResultFields = self.views.date_time_comparison_criteria_view_page
            Custom_ResultFields = ''
        elif criteria_type == 'EXISTS_IN_REFTABLE':
            operators = constants.EXISTS_IN_REFTABLE
            ResultFields = self.views.look_up_reference_table_criteria_view_page
            Custom_ResultFields = ''
        elif criteria_type == 'CUSTOM':
            operators = {}
            ResultFields = ''
            Custom_ResultFields = self.views.custom_criteria_view_page
        I_CONTEXT_ID = request.get('I_CONTEXT_ID','')
        src = request.get('src','')
        header = self.ZeUI.getHeader()
        footer = self.ZeUI.getFooter()
        dec_table_id = request.get('dec_table_id','')
        clauses_records = self.Sentinel.SentinelModel.\
                        selectCriteriaDetails(\
                            criteria_id=criteria_id,
                            rule_enabled='N',
                            dec_table_id=dec_table_id,
                            query_from=1,
                            query_to=1).dictionaries()

        additional_value = ''
        if (clauses_records[0]['ADDITIONAL_VALUES']):
            additional_value = eval(clauses_records[0]['ADDITIONAL_VALUES'])
        entity_attr_idn = clauses_records[0]['SRE_ENTITY_IDN1']
        ident_custom_pattern = EntityAttr.load(self, idn=entity_attr_idn).populate_additional_values()
        label={}
        custom_default_fields = {}
        for i in range(len(ident_custom_pattern)):
            label[ident_custom_pattern[i].split(':')[0][3:-1]] = ident_custom_pattern[i].split(':')[2][1:-3]
            custom_default_fields[ident_custom_pattern[i].split(':')[0][3:-1]] = ident_custom_pattern[i].split(':')[1]
        criteriatype = self.getCriteriaType()
        dec_table_id =  request.get('dec_table_id','')
        decColDetails = ''
        if dec_table_id:
            operators = constants.DECISION_TABLE_OPERATORS_DICT
            Custom_ResultFields=''
            ResultFields=''
            decColDetails = self.getDecTableColumns(dec_table_id=dec_table_id, template_call = 'Y')
        current_page = {True: 'criteria_view', False: 'criteria_decision_view'}[request.get('dec_table_id','') == '']
        dtml_document = getattr(self.views, current_page)
        next_page = header+dtml_document(self.views,
                                         REQUEST = request,
                                         criteria_id=criteria_id,
                                         clauses_records=clauses_records,
                                         I_CONTEXT_ID=I_CONTEXT_ID,
                                         operators=operators,
                                         criteriatype=criteriatype,
                                         additional_criteria=additional_criteria,
                                         label=label,
                                         decColDetails=decColDetails,
                                         additional_value=additional_value,
                                         dec_table_id=dec_table_id,
                                         custom_default_fields=custom_default_fields,
                                         Custom_ResultFields=Custom_ResultFields,
                                         ResultFields=ResultFields
                                         )+footer
        return next_page

    @normalize_form(('criteria_operator'))    
    def updateCriteria(self):
        """
        @description : This method is used to show edit criteria page.
        @return : return criteria edit page
        """
        request = self.REQUEST
        message = ''
        try:
            user_id = int(self.cms.ZeUser.Model.getLoggedinUserIdn())
        except:
            user_id = 3
        I_CONTEXT_ID = request.get('I_CONTEXT_ID','')
        upd_criteria_title = request.get('criteria_title','').strip()
        criteria_description = request.get('criteria_description','').strip()
        criteria_type = request.get('criteria_type','')                 
        criteria_id = request.get('criteria_id','')
        criteria_operator = request.get('criteria_operator','')
        criteria_value = request.get('criteria_value','').strip()
        entity = request.get('entity','')
        source = request.get('source','')
        entity_attribute = request.get('entity_attribute','')
        reftblcolumn = request.get('refcolumn','')
        reftbl = request.get('reftbl','')
        criteria_description = request.get('criteria_description','').strip()
        additional_value = ''
        ident_custom_pattern = ''
        condition_criteria = ''
        operators = constants.VALID_ATTRIBUTE_OPERATORS_DICT
        if criteria_operator:
            criteria_operator = operators[criteria_operator]
        if criteria_type =='CUSTOM':
            ident_custom_pattern = EntityAttr.load(self, idn=entity_attribute).populate_additional_values()
            label={}
            for i in range(len(ident_custom_pattern)):
                label['x'+str(i)] = ident_custom_pattern[i].split(':')[2][1:-2]
            additional_value = {}
            #val_lst = ['','']
            for i in range(len(ident_custom_pattern)):
                cust_value = request['x'+str(i+1)].strip()
                if re.findall("'",cust_value):
                    additional_value['x'+str(i+1)] = cust_value
                if not cust_value.startswith("'") and\
                   (not (cust_value.startswith("(") and cust_value.endswith(")")))\
                   and (not re.match("^[0-9]*$", cust_value)):
                    cust_value = "'"+cust_value+"'"
                additional_value['x'+str(i+1)] = ast.literal_eval(cust_value)

                #if ((cust_value.startswith("(") and cust_value.endswith(")")))\
                   #and (not re.findall(",", cust_value)):
                    #val = cust_value[1:-1]
                    #if re.findall("'",val):
                        #val_lst[0] = cust_value[2:-2]
                    #else:
                        #val_lst[0] = val
                    #additional_value['x'+str(i+1)] = tuple(val_lst)
                #else:
                    #additional_value['x'+str(i+1)] = ast.literal_eval(cust_value)

        if criteria_operator=='no operator':
            reftblcolumn = ''
            reftbl = ''
            criteria_value = ''
            condition_criteria = 0
            criteria_operator = {True: '', False: criteria_operator}[criteria_type == 'CUSTOM']
        if criteria_type=='EXISTS_IN_REFTABLE':
            criteria_value = ''
            condition_criteria = 1
            additional_value = ''
        if source=='source_static':
            reftblcolumn = ''
            reftbl = ''
            condition_criteria = 0

        # Following inputs are being used for date time criteria
        from_dt = ''
        to_dt = ''

        if source=='source_absolute_datetime':
            reftblcolumn = ''
            reftbl = ''
            criteria_value = ''
            condition_criteria = 0

            absolute_from_date = request.get('absolute_from_date','')
            absolute_from_hrs = request.get('absolute_from_hrs','')
            absolute_from_min = request.get('absolute_from_min','')
            absolute_from_ampm = request.get('absolute_from_ampm','')

            absolute_to_date = request.get('absolute_to_date','')
            absolute_to_hrs = request.get('absolute_to_hrs','')
            absolute_to_min = request.get('absolute_to_min','')
            absolute_to_ampm = request.get('absolute_to_ampm','')

            if absolute_from_date and absolute_from_hrs and absolute_from_min:
                from_dt_str = "%s %s:%s:00 %s" % (absolute_from_date,
                                                  absolute_from_hrs,
                                                  absolute_from_min,
                                                  absolute_from_ampm)
                #parse time using 12 hour clock
                parsed_from_dt = datetime.strptime(from_dt_str,
                                                   "%m/%d/%Y %I:%M:%S %p")
                from_dt = parsed_from_dt.strftime("%m/%d/%Y %H:%M:%S")

            if absolute_to_date and absolute_to_hrs and absolute_to_min:
                to_dt_str = "%s %s:%s:00 %s" % (absolute_to_date,
                                                absolute_to_hrs,
                                                absolute_to_min,
                                                absolute_to_ampm)
                #parse time using 12 hour clock
                parsed_to_dt = datetime.strptime(to_dt_str,
                                                 "%m/%d/%Y %I:%M:%S %p")
                to_dt = parsed_to_dt.strftime("%m/%d/%Y %H:%M:%S")

        if source == 'source_relative_datetime':
            reftblcolumn = ''
            reftbl = ''
            criteria_value = ''
            condition_criteria = 0

            lookback_period = request.get('lookback_period','')
            relative_type = request.get('relative_type','')

            relative_date = request.get('relative_date','')
            relative_hrs = request.get('relative_hrs','')
            relative_min = request.get('relative_min','')
            relative_ampm = request.get('relative_ampm','')

            if (relative_type and lookback_period):
                if (relative_date and relative_hrs and relative_min):

                    to_dt_str = "%s %s:%s:00 %s" % (relative_date,
                                                    relative_hrs,
                                                    relative_min,
                                                    relative_ampm)
                    # parse the to_dt string using 12 hour clock
                    new_from_dt = datetime.strptime(to_dt_str, "%m/%d/%Y %I:%M:%S %p")
                    to_dt = new_from_dt.strftime("%m/%d/%Y %H:%M:%S")

                    if relative_type in constants.unit_limits:
                        from_dt = new_from_dt - timedelta(hours=int(constants.unit_limits[relative_type])*int(lookback_period))

                    if relative_type == 'Month(s)':
                        mx_new_from_dt = mx_date_time(new_from_dt.year,
                                                      new_from_dt.month,
                                                      new_from_dt.day,
                                                      new_from_dt.hour,
                                                      new_from_dt.minute,
                                                      new_from_dt.second)
                        from_dt =  mx_new_from_dt - RelativeDateTime(months=int(lookback_period))

                    if relative_type == 'Year(s)':
                        mx_new_from_dt = mx_date_time(new_from_dt.year,
                                                      new_from_dt.month,
                                                      new_from_dt.day,
                                                      new_from_dt.hour,
                                                      new_from_dt.minute,
                                                      new_from_dt.second)
                        from_dt = mx_new_from_dt - RelativeDateTime(years=int(lookback_period))

                    from_dt = from_dt.strftime("%m/%d/%Y %H:%M:%S")

                criteria_value = str(lookback_period)+'@@'+str(relative_type)

        if criteria_type == 'TEST_AGAINST_COLUMN':
            tot_recs = int(request.get('conditionCount', ''))
            dec_table_id = request.get('dec_table_id' , '')
            dec_tble_operators = constants.DECISION_TABLE_OPERATORS_DICT
            rowCount = request.get('rowCount', '')
            col_details = self.getDecTableColumns(dec_table_id=dec_table_id,template_call = 'Y')
            for i in range(tot_recs):
                entity_column = request.get('entity_attribute_r'+str(i+1), '')
                new_operator = request.get('criteria_operator_r'+str(i+1), '')
                if new_operator:
                    new_operator = dec_tble_operators[new_operator]
                dec_column_num = request.get('dec_column_name_r'+str(i+1), '')
                criteria_title = request.get('criteria_title','').strip()
                mod_criteria_title = criteria_title+'_'+col_details[dec_column_num]+'_op( '+new_operator+' )'
                values = Decisiontable.load(self, idn=dec_table_id).fetch_values_down_column(tbl_colno = int(dec_column_num))
                data = CriterionTestAgainstTableColumn.convert_params_to_coldata(values, new_operator)
                criteria_id = request.get('criteria_idR'+str(i+1), '')
                if criteria_id:
                    result = self.Sentinel.SentinelModel.updateCriteria(criteria_id=criteria_id,
                                                                        operator=new_operator,
                                                                        title=mod_criteria_title,
                                                                        value=criteria_value,
                                                                        description=criteria_description,
                                                                        criteria_type = criteria_type,
                                                                        reftblcolumn = reftblcolumn,
                                                                        reftbl = reftbl,
                                                                        entity_attribute = entity_column,
                                                                        user_id=user_id,
                                                                        from_date=from_dt,
                                                                        to_date=to_dt,
                                                                        additional_values=additional_value,
                                                                        dec_table_id=dec_table_id,
                                                                        dec_column_num=dec_column_num)
                    Decisiontable.load(self, idn=dec_table_id).refresh_all_columnar_criteria()
                else:
                    criteria_title = request.get('criteria_title','').strip()
                    col_details = self.getDecTableColumns(dec_table_id=dec_table_id,template_call = 'Y')
                    entity_column = request.get('entity_attribute_r'+str(i+1), '')
                    entity_attr_details = self.Sentinel.SentinelModel.getCriteriaEntityValuesForDecTable(entity_idn=entity_column).dictionaries()
                    new_operator = request.get('criteria_operator_r'+str(i+1), '')
                    if new_operator:
                        new_operator = dec_tble_operators[new_operator]
                    dec_column_num = request.get('dec_column_name_r'+str(i+1), '')
                    mod_criteria_title = criteria_title+'_'+col_details[dec_column_num]+'_op( '+new_operator+' )'
                    # Since we are creating new criteria - we need to create external cd
                    ext_criteria_cd = "CRITERIA"+get_base_external_cd(self)
                    criteriaId = Decisiontable.load(self, idn=dec_table_id).create_columnar_criterion(title=mod_criteria_title,
                                                                                                      entity_name= entity_attr_details[0]['NAME'],
                                                                                                      entity_attr= entity_attr_details[0]['ENTITY_ATTR'],
                                                                                                      binary_op= new_operator,
                                                                                                      tbl_colno= int(dec_column_num),
                                                                                                      ext_criteria_cd=ext_criteria_cd)

        else:
            result = self.Sentinel.SentinelModel.updateCriteria(criteria_id=criteria_id,
                                                                title=upd_criteria_title,
                                                                value=criteria_value,
                                                                operator=criteria_operator,
                                                                description=criteria_description,
                                                                criteria_type = criteria_type,
                                                                reftblcolumn = reftblcolumn,
                                                                reftbl = reftbl,
                                                                entity_attribute = entity_attribute,
                                                                user_id=user_id,
                                                                from_date=from_dt,
                                                                to_date=to_dt,
                                                                additional_values=additional_value)

        self.Sentinel.SentinelModel.deActivateConditionalCriteria(criteria_idn = criteria_id)

        # Additional conditions used for reference table
        if condition_criteria:
            self.addCriteriaAdditionalCondition(criteria_id=criteria_id,user_id=user_id)
        if criteria_type == 'TEST_AGAINST_COLUMN':
            request.set('dec_table_id', dec_table_id)
            request.set('I_CONTEXT_ID',I_CONTEXT_ID)
            request.set('src','updateCriteria')
            request.set('criteria_title', upd_criteria_title)
            return self.showCriteriaEditPage()
        else:
            request.set('criteria_id',criteria_id)
            request.set('I_CONTEXT_ID',I_CONTEXT_ID)
            request.set('src','updateCriteria')
            return self.showCriteriaEditPage()
        
    @normalize_form() 
    def addCriteriaAdditionalCondition(self,criteria_id,user_id):
        """
        @description : This method is used to Add Criteria Additional Condition.
        @param : criteria_id {int} criteria id
        @param : user_id {int} user id
        """
        request = self.REQUEST
        reftable_conditions_len = request.get('additional_criteria',0)
        if reftable_conditions_len:
            operators = constants.VALID_ATTRIBUTE_OPERATORS_DICT
            for each_cond in range(1,int(reftable_conditions_len)+1):
                reftable_condition_operator_req_var = 'add_cond_operator'+str(int(each_cond))
                selected_operator = request.get(reftable_condition_operator_req_var,'')
                reftable_condition_value_req_var = 'add_cond_value'+str(int(each_cond))
                selected_value = request.get(reftable_condition_value_req_var,'')
                reftable_condition_column_req_var = 'add_cond_refcolumn'+str(int(each_cond))
                selected_refcol = request.get(reftable_condition_column_req_var,'')
                if selected_operator and selected_value and selected_refcol:
                    operator = operators[selected_operator]
                    self.Sentinel.SentinelModel.insertConditionalCriteria(
                        criteria_id=criteria_id,
                        value=selected_value,
                        refcolumn=selected_refcol,
                        user_id=user_id,
                        operator=operator,
                        entity_active='Y')

    def getRefTables(self,template_call='N'):
        """
        @description : This method is used to get reference table.
        @param : template_call - default - 'N' a js call
        @return : return table name for drop down.
        """
        ref_tbl_id = self.REQUEST.get('ref_tbl_id','')
        result_query = self.Sentinel.SentinelModel.getRefTableNames().dictionaries()
        if template_call == 'N':
            result_set='<select id="reftbl_lst" align="left" onChange="$SENTINEL.datatable(this.options[this.selectedIndex].value, \' \', \'refGridResult\')">'
            result_set+='<option value="">---Select One---</option>'
            for rs in result_query:
                result_set+="<option value=\'"+str(rs['ID'])+"'"
                if str(ref_tbl_id) == str(rs['ID']):
                    result_set+="SELECTED=SELECTED"
                result_set+=">"+str(rs['TITLE'])+"</option>"
            result_set+='</select>'
            return result_set
        else:
            return result_query

    def getDecisionTables(self,template_call='N'):
        """
        @description : This method is used to get Decision table.
        @param : template_call - default - 'N' a js call
        @return : return table name for drop down.
        """
        dec_tbl_id = self.REQUEST.get('dec_tbl_id','')
        result_query = self.Sentinel.SentinelModel.getDecisionTableNames().dictionaries()
        """if template_call == 'N':
            result_set='<select id="dectbl_lst" align="left" onChange="$SENTINEL.datatable(this.options[this.selectedIndex].value, \'decGridResult\')">'
            result_set+='<option value="">---Select One---</option>'
            for rs in result_query:
                result_set+="<option value=\'"+str(rs['ID'])+"'"
                if str(dec_tbl_id) == str(rs['ID']):
                    result_set+="SELECTED=SELECTED"
                result_set+=">"+str(rs['TITLE'])+"</option>"
            result_set+='</select>'
            return result_set
        else:"""
        return result_query

    def getActivityAssignToList(self):
        """
        @description : This method is used to get activity assign to list
        @return : return Assign to List for an activity
        """
        worklist_dict={}
        assign_to_dict={}
        for r in self.Sentinel.SentinelModel.getworklist().dictionaries():
            worklist_dict[str(r['SYS_USER_ID'])+str('@@WORKLIST')]=str(r['SYS_USER_ID'])+str('(')+str('WORKLIST')+str(')')
        assign_to=constants.activity_assign_to_list
        for i in assign_to:
            assign_to_dict[i]=i
        assign_to_dict.update(worklist_dict)
        return assign_to_dict


    def get_batch_activity_assign_to_list(self):
        """
        @description : This method is used to get activity assign to list
        @return : return Assign to List for an activity
        """
        worklist_dict={}
        assign_to_dict={}
        for r in self.Sentinel.SentinelModel.getworklist().dictionaries():
            worklist_dict[str(r['SYS_USER_ID'])+str('@@WORKLIST')]=str(r['SYS_USER_ID'])+str('(')+str('WORKLIST')+str(')')
        assign_to=constants.batch_activity_assign_to_list
        for each in assign_to:
            assign_to_dict[each]=each
        assign_to_dict.update(worklist_dict)
        return assign_to_dict    
    # Action Related Method are Started Here

    def showActionPage(self):
        """
        @description : This method is used to show action search page.
        @return : return to action search page.
        """
        request = self.REQUEST
        header_type = ''
        if request.has_key('header_type'):
            header_type = request['header_type']
        header = self.ZeUI.getHeader(header_type)
        footer = self.ZeUI.getFooter(header_type)
        I_CONTEXT_ID = request.get('I_CONTEXT_ID','')
        dtml_document = getattr(self.views, 'action_search')
        next_page = header+dtml_document(self.views, 
                                         REQUEST=request,
                                         I_CONTEXT_ID=I_CONTEXT_ID
                                         )+footer
        return next_page

    def getActionScripts(self):
        """
        @description : This method is used to Gets the list of methods from action_registry
                       and sorts the dict and returns list of tuples
        @return : This function gets the list of methods from action_registry
                    and sorts the dict and returns list of tuples
        """
        action_scripts = self.SentinelEngine.SentinelActions.action_registry
        return self.ZeUtil.sortDict(action_scripts.items())

    def showActionAddPage(self):
        """
        @description : This method is used to show action add page.
        @return : return to action add page.
        """
        request = self.REQUEST
        header_type = ''
        if request.has_key('header_type'):
            header_type = request['header_type']
        header = self.ZeUI.getHeader(header_type)
        footer = self.ZeUI.getFooter(header_type)
        dtml_document = getattr(self.views, 'action_add')
        return header+dtml_document(self.views,REQUEST = request)+footer

    @normalize_form()     
    def addAction(self,
                  fromInstaller=''
                  ):
        """
        @description : This method is used to add action
        @return : return to action edit page.
        """
        request = self.REQUEST
        message = self.ZeUtil.getJivaMsg(msg_code = '694')
        param_list = []
        new_parameter_set = ''
        action_script_idn = request.get('action_script_idn','')
        sel_div_index = request.get('I_SEL_DIV_INDEX','')
        sel_dec_table = request.get('dec_table_idn','')
        sel_dec_table_column_num = request.get('dec_table_column_num','')
        sel_param_name = request.get('I_PARAM_NAME','')
        param_name = ''

        try:
            user_id = int(self.cms.ZeUser.Model.getLoggedinUserIdn())
        except:
            user_id = 3
        action_title = request.get('new_action_title','').strip()
        action_script = request.get('new_action_script','')
        action_desc = request.get('new_action_description','').strip()
        data = ''
        dec_table_idn = ''
        dec_tbl_col_idn = ''
        if sel_div_index:
            dec_table_idn  = request[sel_dec_table]
            dec_tbl_col_idn = request[sel_dec_table_column_num]
            param_name = request[sel_param_name]
        if dec_table_idn and dec_tbl_col_idn and sel_param_name:
            if isinstance(action_script_idn,str):
                action_script_idn = [action_script_idn] # type casting str to list
            dectable = Decisiontable.load(self, idn=dec_table_idn)
            values = dectable.fetch_values_down_column(int(dec_tbl_col_idn))
            data = Action.convert_params_to_coldata(values,param_name)
            action_script_idn.extend(['I_SEL_DIV_INDEX',
                                      request['dec_table_idn'],
                                      request['dec_table_column_num'],
                                      request['I_PARAM_NAME']])
        if action_script_idn:
            if isinstance(action_script_idn,str):
                new_action_script_value = action_script_idn+'='+\
                                        request.get(action_script_idn,'')
                
                param_list.append(new_action_script_value)
            elif sel_param_name:
                param_list=[str(each)+'='+str(request.get(each,''))\
                            for each in action_script_idn \
                            if each !='alert_message' and (str(each) <> param_name)]
            else:
                param_list=[str(each)+'='+str(request.get(each,''))\
                            for each in action_script_idn \
                            if each !='alert_message']
                
                if request.get('start_date','') and request.get('end_date',''):
                    new_start_date = "%s %s:%s:00 " % (request.get('start_date',''),
                                                request.get('start_hrs',''),
                                                request.get('start_min',''))
                    new_end_date = "%s %s:%s:00 " % (request.get('end_date',''),
                                                request.get('end_hrs',''),
                                                request.get('end_min',''))
                    
                    param_list.append('new_start_date'+'='+new_start_date)
                    param_list.append('new_end_date'+'='+new_end_date)

        ext_action_cd = "ACTION"+get_base_external_cd(self)

        if dec_table_idn:
            actionIdObj =  Action.insert(
                self,
                title=action_title,# should be name of column in table, for UI to use?
                desc=action_desc,
                scriptname=action_script,
                tbl_idn=dec_table_idn,
                tbl_colno=dec_tbl_col_idn,
                tbl_coldata=data,
                ext_action_cd = ext_action_cd
            )
            action_id = actionIdObj.idn
        else:
            actionId = self.Sentinel.SentinelModel.insertActionDetails(\
                title=action_title,
                script=action_script,
                description=action_desc,
                user_id = user_id,
                ext_action_cd = ext_action_cd)
            action_id = actionId[0]['sre_action_idn']

        if request.has_key('alert_message'):
            if request['alert_message']!='FRMInstallScript':
                new_parameter_set = self.addAlertActionScript(\
                    action_id,
                    user_id,
                    entity_active='Y'
                )
        parameter_list = request.get('new_action_pnames',param_list)
        if new_parameter_set:
            new_parameter_set = self.addActionParameters(action_id,\
                                                         parameter_list,
                                                         user_id,
                                                         dup_param_set = 'Y'
                                                         )
        else:
            new_parameter_set = self.addActionParameters(action_id,\
                                                         parameter_list,
                                                         user_id
                                                         )
        return action_id

    def showActionEditPage(self):
        """
        @description : This method is used to show action edit page.
        @return : return to action edit page.
        """
        request = self.REQUEST
        pop_up = request.get('pop_up','')
        row_index = request.get('row_index',0)
        tabl_name = request.get('tabl_name',0)
        src = request.get('src','')
        msg_code = {'addAction':'695','updateAction':'696'}
        if src:
            request.set('info_alert', self.ZeUtil.getJivaMsg(msg_code = msg_code[src]))
        header = self.ZeUI.getHeader()
        footer = self.ZeUI.getFooter()
        I_CONTEXT_ID = request.get('I_CONTEXT_ID','')
        action_id = request.get('action_id',0)
        dec_table_idn  = ''
        sel_div_index = ''
        param_name = ''
        param_list = {}
        param_set = self.Sentinel.SentinelModel.selectActionParams(\
            action_idn = action_id).dictionaries()

        if param_set:
            for param in param_set:
                if param['PARAM_NAME'] and param['PARAM_VALUE']:
                    param_list[param['PARAM_NAME']] =\
                              param['PARAM_VALUE']
            if param_list.has_key('I_SEL_DIV_INDEX') and param_list['I_SEL_DIV_INDEX']:
                sel_div_index = param_list['I_SEL_DIV_INDEX']
                dec_table_idn = param_list['dec_table_idn'+sel_div_index]
                dec_table_colno = param_list['dec_table_column_num'+sel_div_index]
                param_name = param_list['I_PARAM_NAME'+sel_div_index]
        tempname = request.get('tempname','')
        dtml_document = getattr(self.views,'action_edit')
        next_page = header+dtml_document(self.views,
                                         request=request,
                                         pop_up=pop_up,
                                         row_index=row_index,
                                         tabl_name=tabl_name,
                                         action_id=action_id,
                                         I_CONTEXT_ID=I_CONTEXT_ID,
                                         tempname=tempname,
                                         I_SEL_DIV_INDEX=sel_div_index,
                                         I_DEC_TABLE_IDN_WITH_INDEX=dec_table_idn,
                                         I_PARAM_NAME=param_name
                                         )+footer
        return next_page

    def showActionViewPage(self):
        """
        @description : This method is used to show action edit page.
        @return : return to action edit page.
        """
        request = self.REQUEST
        src = request.get('src','')
        header = self.ZeUI.getHeader()
        footer = self.ZeUI.getFooter()
        I_CONTEXT_ID = request.get('I_CONTEXT_ID','')
        action_id = request.get('action_id',0)
        tempname = request.get('tempname','')
        clauses_records = self.Sentinel.SentinelModel.\
                        selectDetailedActions(
                            action_id=action_id,
                            rule_enabled='N',
                            query_from=1,
                            query_to=1).dictionaries()
        for actionid in clauses_records:
            actionid['ACTION_ID'] = actionid['IDN']
            param_list = []
            param_set = self.Sentinel.SentinelModel.selectActionParams(\
                action_idn = actionid['IDN']).dictionaries()
            if param_set:
                for param in param_set:
                    if param['PARAM_NAME'] and param['PARAM_VALUE']:
                        param_list.append('%s=%s' % (param['PARAM_NAME'],\
                                                     param['PARAM_VALUE']))
                actionid['parameter_details'] = param_list
            else:
                actionid['parameter_details'] = []
        dtml_document = getattr(self.views,'action_view')
        next_page = header+dtml_document(self.views,
                                         request=request,
                                         action_id=action_id,
                                         clauses_records=clauses_records,
                                         rule_enabled='N',
                                         I_CONTEXT_ID=I_CONTEXT_ID,
                                         tempname=tempname
                                         )+footer
        return next_page

    @normalize_form()     
    def updateAction(self):
        """
        @description : This method is used to update action.
        @return : return to action edit page.
        """
        request = self.REQUEST
        param_list = []
        new_parameter_set = ''
        pop_up = request.get('pop_up','')
        action_script_idn = request.get('action_script_idn','')
        action_id = request.get('actionID','')
        action_script = request.get('action_script','')
        I_CONTEXT_ID = request.get('I_CONTEXT_ID','')
        sel_div_index = request.get('I_SEL_DIV_INDEX','')
        sel_dec_table = request.get('dec_table_idn','')
        sel_dec_table_column_num = request.get('dec_table_column_num','')
        sel_param_name = request.get('I_PARAM_NAME','')
        action_title = request.get('new_action_title','').strip()
        action_script = request.get('new_action_script','')
        action_desc = request.get('new_action_description','').strip()
        dec_table_idn = ''
        dec_tbl_col_num = ''
        dec_tbl_coldata = ''
        if action_script_idn and sel_param_name:
            if isinstance(action_script_idn,str):
                action_script_idn = [action_script_idn] # type casting str to list
            action_script_idn.extend(['I_SEL_DIV_INDEX',
                                      request['dec_table_idn'],
                                      request['dec_table_column_num'],
                                      request['I_PARAM_NAME']])

        try:
            user_id = int(self.cms.ZeUser.Model.getLoggedinUserIdn())
        except:
            user_id = 3
        if action_script_idn:
            if isinstance(action_script_idn,str):
                new_action_script_value = action_script_idn+'='+\
                                        request.get(action_script_idn,'')
                param_list.append(new_action_script_value)

            elif sel_param_name:
                param_list = [str(each) + '=' + str(request.get(each,''))\
                              for each in action_script_idn \
                              if each != ('alert_idn' or 'alert_message') and (str(each) <> request[sel_param_name])]
            else:                                
                param_list = [str(each) + '=' + str(request.get(each,''))\
                              for each in action_script_idn \
                              if each != ('alert_idn' or 'alert_message')]
                
            if request.get('start_date','') and request.get('end_date',''):
                    new_start_date = "%s %s:%s:00 " % (request.get('start_date',''),
                                                request.get('start_hrs',''),
                                                request.get('start_min',''))
                    new_end_date = "%s %s:%s:00 " % (request.get('end_date',''),
                                                request.get('end_hrs',''),
                                                request.get('end_min',''))
                    param_list.append('new_start_date'+'='+new_start_date)
                    param_list.append('new_end_date'+'='+new_end_date)

        self.SentinelModel.deActivateActionParams(action_id)
        if request.has_key('alert_message'):
            new_parameter_set = self.addAlertActionScript(\
                action_id,
                user_id,
                entity_active='Y'
            )
        parameter_list = request.get('new_action_pnames',param_list)
        if new_parameter_set:
            new_parameter_set = self.addActionParameters(\
                action_id,
                parameter_list,
                user_id,
                dup_param_set = 'Y'
            )
        else:
            new_parameter_set = self.addActionParameters(\
                action_id,
                parameter_list,
                user_id
            )
        updated_description = request.get('new_action_description','').strip()
        updated_act_title = request.get('new_action_title','').strip()

        self.Sentinel.SentinelModel.updateActionDetails(\
            id=action_id,
            action_title=updated_act_title,
            description=updated_description,
            user_id=user_id,
        )
        if sel_param_name:
            dec_table_idn = request[request['dec_table_idn']]
            dec_tbl_col_num = request[request['dec_table_column_num']]
            param_name = request[sel_param_name]
            if Action.load_many(self, tbl_idn=dec_table_idn, idn=action_id, is_active = 'Y'):
                action_object = Action.load_many(self, tbl_idn=dec_table_idn, idn=action_id, is_active = 'Y')[0]
            else:
                action_object = Action.load_many(self, idn=action_id, is_active = 'Y')[0]
            action_object.tbl_idn = dec_table_idn
            action_object.tbl_colno = dec_tbl_col_num
            dectable = Decisiontable.load(self, idn=dec_table_idn)
            values = dectable.fetch_values_down_column(int(dec_tbl_col_num))
            action_object.tbl_coldata = Action.convert_params_to_coldata(values,param_name)
            action_object.save()

        request.set('src','updateAction')
        request.set('action_id',action_id)
        request.set('I_CONTEXT_ID',I_CONTEXT_ID)
        return self.showActionEditPage()

    def addAlertActionScript(self,
                             action_script_idn,
                             user_id,
                             entity_active
                             ):
        """
        @description : This method is used to processes code_alerts, sentinel_action_params
                       and sentinel_actions_master when we have choosen action script as Add Alerts.

        @param : action_script_idn {int} action script table id
        @param : user_id {int} user id
        @param : entity_active {string} either 'Y/N'
        @return : return parameter set.
        """
        request = self.REQUEST
        alert_prior = request.get('alert_priority','1')
        alert_priority = alert_prior.split('+')[0]
        parameter_string = []
        if request.has_key('alert_message'):
            alert_message = request.get('alert_message')
        elif request.has_key('alert_idn'):
            alert_message = request.get('alert_idn')
        if alert_message == '':
            alert_message = '-'
        if alert_message:
            parameter_string.append('alert_message'+"="+str(alert_message))
            if action_script_idn:
                new_parameter_set = self.addActionParameters(\
                    action_script_idn,
                    parameter_string,
                    user_id,
                    dup_param_set='Y',
                    entity_active=entity_active
                )
            else:
                new_parameter_set = self.addActionParameters(\
                    action_script_idn,
                    parameter_string,
                    user_id,
                    entity_active=entity_active
                )
        return new_parameter_set

    @normalize_form()     
    def addActionParameters(self,
                            action_script_idn,
                            raw_parameters_list,
                            user_id='',
                            dup_param_set='',
                            entity_active=''
                            ):
        """
        @description : This method is used to Add action parameter

        @param : action_script_idn {int} action script idn.
        @param : raw_parameters_list {string} parameter list.
        @param : user_id {int} user id
        @param : dup_param_set {string} param set.
        @param : entity_active {string} either 'Y/N'
        @return : return parameter set value
        """
        processed_parameters = []
        for eachRawParameter in raw_parameters_list:
            eachRawParameterList = eachRawParameter.split('=')
            if len(eachRawParameterList) == 2:
                processed_parameters.\
                                    append((eachRawParameterList[0],eachRawParameterList[1]))
        if processed_parameters:
            i = 0
            for name,value in processed_parameters:
                self.Sentinel.SentinelModel.insertActionParameters(\
                    action_script_idn=action_script_idn,
                    parameter_name=name,
                    parameter_value=value,
                    user_id=user_id,
                    entity_active='Y'
                )
                i=i+1
        else:
            self.Sentinel.SentinelModel.insertActionParameters(\
                action_script_idn=action_script_idn,
                user_id=user_id,
                entity_active='Y'
            )
        return

    def getActionParamsPage(self,
                            sel_script_name=None,
                            parameter_details=[],
                            I_UPDT_FORM_NAME = ''
                            ):
        """
        @description : This method is used to get action parameters page for the selected action script

        @param : sel_script_name {string} script name.
        @param : parameter_details {string} parameter list.
        @return : return page based on action script.
        """
        request = self.REQUEST
        views = self.views.views_act_types
        I_CONTEXT_ID = request.get('I_CONTEXT_ID','')
        I_FORM_NAME = request.get('I_FORM_NAME','')
        if not I_FORM_NAME:
            I_FORM_NAME = I_UPDT_FORM_NAME + I_CONTEXT_ID
        new_action_script = self.SentinelEngine.SentinelActions.\
                          action_registry.get(\
                              request.get('new_action_script',None), None)
        if sel_script_name:
            sel_script_name = self.SentinelEngine.\
                            SentinelActions.action_registry.get(\
                                sel_script_name,None)
        act_param_details = {}
        act_param_pages = views.objectIds()
        for each in parameter_details:
            temp = each.split('=')
            act_param_details[temp[0]] = temp[1]
        if (sel_script_name or new_action_script):
            script_name = 'act_param_' + (sel_script_name or new_action_script)
            if script_name in act_param_pages:
                dtml_document = getattr(views, script_name)
                return dtml_document(views,
                                     act_param_details = act_param_details,
                                     I_CONTEXT_ID = I_CONTEXT_ID,
                                     I_FORM_NAME = I_FORM_NAME,
                                     REQUEST=request
                                     )
            else:
                return views.act_param_none()
        else:
            return views.act_param_none()

    def getActionResultPage(self, actionID='', extCall = 'N'):
        """
        @description : This method is used to get action result page.

        @param : actionID {int} action id.
        @param : extCall {string} either 'Y/N'.
        @return : return action result page.
        """
        request = self.REQUEST
        header = self.ZeUI.getHeader()
        footer = self.ZeUI.getFooter()
        action_script = request.get('action_script','').strip()
        checked_chkbox = request.get('checked_chkbox','')
        action_title = self.ZeUtil.replaceQuotes(request.get('action_title','').strip())
        rule_enabled = request.get('filter_enabled','Y').strip()
        noResultMsg=self.ZeUtil.getJivaMsg(msg_code='627')

        # pagination
        page_info = self.getPageDetails()
        total_count = self.Sentinel.SentinelModel.\
                    selectDetailedActionsCount(
                        action_id=actionID,
                        action_script=action_script,
                        action_title=action_title,
                        rule_enabled=rule_enabled
                    )

        action_details_list = self.Sentinel.SentinelModel.\
                            selectDetailedActions(
                                action_id=actionID,
                                action_script=action_script,
                                action_title=action_title,
                                rule_enabled=rule_enabled,
                                query_from=page_info['I_START_REC_NO'],
                                query_to=page_info['I_END_REC_NO']
                            )
        action_details_list = action_details_list.dictionaries()
        for actionid in action_details_list:
            actionid['ACTION_ID'] = actionid['IDN']
            param_list = []
            param_set = self.Sentinel.SentinelModel.selectActionParams(\
                action_idn = actionid['IDN']).dictionaries()
            if param_set:
                for param in param_set:
                    if param['PARAM_NAME'] and param['PARAM_VALUE']:
                        param_list.append('%s=%s' % (param['PARAM_NAME'],\
                                                     param['PARAM_VALUE']))
                actionid['parameter_details'] = param_list
            else:
                actionid['parameter_details'] = []
        if extCall == 'N':
            current_page = {True: 'export_action_result_page', False: 'action_result_page'}\
                         [request.get('export_flag','N') == 'Y']
            dtml_document = getattr(self.views, current_page)

            return header+dtml_document(self.views, REQUEST=request,
                                        action_details_list=action_details_list,
                                        filter_enabled=rule_enabled,
                                        i_action_script=action_script,
                                        i_action_title=action_title,
                                        total_rec=len(total_count),
                                        checked_chkbox=checked_chkbox,
                                        I_CUR_PG=page_info['I_CUR_PAGE'],
                                        noResultMsg=noResultMsg
                                        )+footer
        if extCall == 'Y':
            return action_details_list

    def getPageDetails(self):
        """
        @description : This method is used to get page details
        @return : return Current Page Number, Starting Record Numebr, Ending Record Number.
        """
        request = self.REQUEST
        I_CUR_PAGE = int(request.get('I_CUR_PAGE','1'))
        if I_CUR_PAGE>1:
            I_START_REC_NO = (I_CUR_PAGE*self.ZeUI.getDefRecPerPage())-\
                           self.ZeUI.getDefRecPerPage()
        else:
            I_START_REC_NO=0

        I_START_REC_NO = I_START_REC_NO+1
        I_END_REC_NO = I_START_REC_NO + self.ZeUI.getDefRecPerPage()-1
        page_info_dic = {}
        page_info_dic['I_CUR_PAGE'] = I_CUR_PAGE
        page_info_dic['I_START_REC_NO'] = I_START_REC_NO
        page_info_dic['I_END_REC_NO'] = I_END_REC_NO
        return page_info_dic

    def showRulePage(self):
        """
        @description : This method is used to show rule search page.
        @return : return to rule search page.
        """
        request = self.REQUEST
        header_type = ''
        if request.has_key('header_type'):
            header_type = request['header_type']
        header = self.ZeUI.getHeader(header_type)
        footer = self.ZeUI.getFooter(header_type)
        I_CONTEXT_ID = request.get('I_CONTEXT_ID','')
        keywords_rst = self.Sentinel.SentinelModel.getKeywords()
        dtml_document = getattr(self.views, 'rule_search')
        next_page = header+dtml_document(self.views, 
                                         REQUEST=request,
                                         keywords_rst=keywords_rst,
                                         I_CONTEXT_ID=I_CONTEXT_ID
                                         )+footer
        return next_page

    def getRulesResultPage(self, rule_id=''):
        """"
        @description : This method is used to get rules result page.

        @param : rule_id {int} rule id
        @return : return to rules result page.
        """
        request = self.REQUEST
        rule_title = request.get('rule_title','').strip()
        rule_type = request.get('rule_type','')
        rule_execution_type = request.get('rule_execution_type','')
        event_id = request.get('event_title','')
        rule_enabled = request.get('filter_enabled','Y')
        rule_category = request.get('rule_category','')
        rule_keyword = request.get('rule_keyword','')
        rule_action_title = request.get('rule_action_title','')
        rule_id = request.get('rule_id','')
        I_CONTEXT_ID = request.get('I_CONTEXT_ID','')
        checked_chkbox = request.get('checked_chkbox','')
        rule_criteria_tile = request.get('rule_criteria_tile','')
        rule_reftable = request.get('rule_reftable','')
        I_RULE_ATTR_IDN = request.get('I_RULE_ATTR_IDN','')
        rule_src_idn = request.get('rule_src_idn', '')
        rule_output_label = request.get('rule_output_label','')
        if I_RULE_ATTR_IDN:
            attribute_value_idns = str(request.get('attribute_value_idn',[]))[1:-1]
        else:
            attribute_value_idns = ''
        status = request.get('status','')
        if status:
            msg_code = {'activate':'017','deactivate':'016'}
            request.set('info_alert', self.ZeUtil.getJivaMsg(msg_code = msg_code[status.lower()]))
        header = self.ZeUI.getHeader()
        footer = self.ZeUI.getFooter()
        # Based on Input (joining Reference Table and Criteria Table) Started Here
        join_cri_table = 'Y'
        join_ref_table = 'Y'
        if rule_criteria_tile:
            join_ref_table = ''
            if rule_reftable:
                join_ref_table = 'Y'
        if not rule_criteria_tile and not rule_reftable:
            join_cri_table = ''
            join_ref_table = ''
        # Based on Input (joining Reference Table and Criteria Table) Ending Here
        noResultMsg=self.ZeUtil.getJivaMsg(msg_code='470')
        # pagination
        page_info = self.getPageDetails()

        ruleset_count = self.Sentinel.SentinelModel.\
                      selectRuleDetailsCount(\
                          enabled=rule_enabled,
                          rule_category=rule_category,
                          rule_type=rule_type,
                          rule_execution_type=rule_execution_type,
                          event_id=event_id,
                          rule_action_title=rule_action_title,
                          rule_title=rule_title,
                          rule_keyword=rule_keyword,
                          rule_id=rule_id,
                          rule_reftable=rule_reftable,
                          rule_criteria_tile=rule_criteria_tile,
                          join_cri_table=join_cri_table,
                          join_ref_table=join_ref_table,
                          attribute_value_idns=attribute_value_idns,
                          rule_src_idn=rule_src_idn,
                          rule_output_label=rule_output_label
                      )

        new_rule_recordset = self.Sentinel.SentinelModel.\
                           selectRuleDetails(\
                               rule_category=rule_category,
                               rule_type=rule_type,
                               rule_execution_type=rule_execution_type,
                               enabled=rule_enabled,
                               event_id=event_id,
                               rule_title=rule_title,
                               rule_action_title=rule_action_title,
                               query_from=page_info['I_START_REC_NO'],
                               query_to=page_info['I_END_REC_NO'],
                               rule_id = rule_id,
                               rule_keyword=rule_keyword,
                               rule_reftable=rule_reftable,
                               rule_criteria_tile=rule_criteria_tile,
                               join_cri_table=join_cri_table,
                               join_ref_table=join_ref_table,
                               attribute_value_idns=attribute_value_idns,
                               rule_src_idn=rule_src_idn,
                               rule_output_label=rule_output_label
                           )
        new_rule_list = new_rule_recordset.dictionaries()
        total_count = ruleset_count.dictionaries()
        if total_count:
            total_count = ruleset_count[0]['NUMBER_RECORD']

        current_page = {True: 'export_rules_result_page', False: 'rules_result_page'}\
                     [request.get('export_flag','N') == 'Y']
        # Attach Rule
        if request.get('showrule_list','') == 'Y':
            current_page = 'rule_filter'

        dtml_document = getattr(self.views,current_page)
        return header+dtml_document(self.views, REQUEST=request,
                                    new_rule_list=new_rule_list,
                                    rule_type=rule_type,
                                    rule_execution_type=rule_execution_type,
                                    event_title=event_id,
                                    filter_enabled=rule_enabled,
                                    rule_category=rule_category,
                                    rule_action_title=rule_action_title,
                                    noResultMsg=noResultMsg,
                                    total_rec=total_count,
                                    I_CONTEXT_ID=I_CONTEXT_ID,
                                    rule_keyword=rule_keyword,
                                    rule_title=rule_title,
                                    rule_id=rule_id,
                                    rule_reftable=rule_reftable,
                                    rule_criteria_tile=rule_criteria_tile,
                                    checked_chkbox=checked_chkbox,
                                    attribute_value_idns=attribute_value_idns,
                                    I_RULE_ATTR_IDN = I_RULE_ATTR_IDN,
                                    I_CUR_PG=page_info['I_CUR_PAGE'],
                                    rule_src_idn=rule_src_idn
                                    )+footer

    security.declareProtected('Ze Sentinel ViewExportRule', 'showExportRuleSearchPage')
    def showExportRuleSearchPage(self):
        """
        @description : This method is used to show export rule search page.
        @return : return to export rule search page.
        """
        request = self.REQUEST
        header_type = ''
        if request.has_key('header_type'):
            header_type = request['header_type']
        header = self.ZeUI.getHeader(header_type)
        footer = self.ZeUI.getFooter(header_type)
        keywords_rst = self.Sentinel.SentinelModel.getKeywords()
        dtml_document = getattr(self.views, 'export_rule_search')
        next_page = header+dtml_document(self.views, REQUEST=request, keywords_rst=keywords_rst)+footer
        return next_page

    def showRuleExportToXlPage(self):
        """
        This method returns DTML page with content type set as application ms excel.
        DTML page contains all data related to rules selected for export.
        """
        request = self.REQUEST
        selected_rule_ids_str = request.get('cid','')
        selected_rule_ids_list = selected_rule_ids_str.split(',')

        rule_title = request.get('rule_title','').strip()
        rule_type = request.get('rule_type','')
        event_id = request.get('event_title','')
        rule_enabled = request.get('filter_enabled','Y')
        rule_category = request.get('rule_category','')
        rule_keyword = request.get('rule_keyword','')
        rule_action_title = request.get('rule_action_title','')
        checked_chkbox = request.get('checked_chkbox','')
        rule_criteria_tile = request.get('rule_criteria_tile','')
        rule_reftable = request.get('rule_reftable','')
        rule_src_idn = request.get('rule_src_idn', 4)
        join_cri_table = 'Y'
        join_ref_table = 'Y'
        if rule_criteria_tile:
            join_ref_table = ''
            if rule_reftable:
                join_ref_table = 'Y'
        if not rule_criteria_tile and not rule_reftable:
            join_cri_table = ''
            join_ref_table = ''

        page_info = self.getPageDetails()

        ruleset_count = self.Sentinel.SentinelModel.selectRuleDetailsCount(enabled=rule_enabled,
                                                                           rule_category=rule_category,
                                                                           rule_type=rule_type,
                                                                           event_id=event_id,
                                                                           rule_action_title=rule_action_title,
                                                                           rule_title=rule_title,
                                                                           rule_keyword=rule_keyword,
                                                                           rule_id=selected_rule_ids_list,
                                                                           rule_reftable=rule_reftable,
                                                                           rule_criteria_tile=rule_criteria_tile,
                                                                           join_cri_table=join_cri_table,
                                                                           join_ref_table=join_ref_table,
                                                                           rule_src_idn=rule_src_idn
                                                                           )
        # Get rule details for all to be exported (selected) rules
        rule_result_set = self.Sentinel.SentinelModel.selectRuleDetails(rule_category=rule_category,
                                                                        rule_type=rule_type,
                                                                        enabled=rule_enabled,
                                                                        event_id=event_id,
                                                                        rule_title=rule_title,
                                                                        rule_action_title=rule_action_title,
                                                                        query_from=page_info['I_START_REC_NO'],
                                                                        query_to=ruleset_count[0][0],
                                                                        rule_id=selected_rule_ids_list,
                                                                        rule_keyword=rule_keyword,
                                                                        rule_reftable=rule_reftable,
                                                                        rule_criteria_tile=rule_criteria_tile,
                                                                        join_cri_table=join_cri_table,
                                                                        join_ref_table=join_ref_table,
                                                                        rule_src_idn=rule_src_idn
                                                                        )

        rule_details = rule_result_set.dictionaries()
        # If no matching rule records found, raise error
        if not rule_details:
            raise Exception("No rule details found")

        rule_ids = []
        for eachRule in rule_details:
            rule_id = eachRule['ID']
            rule_ids.append(rule_id)

            # Get all active keywords associated with rule
            rule_keyword_result_set = self.Sentinel.SentinelModel.getRuleKeywords(rule_id=rule_id, entity_active='Y')

            rule_keywords = '@@'.join([each_kw['KEYWORD_DESC'] for each_kw in rule_keyword_result_set])
            eachRule.update({'KEYWORD_DESC':rule_keywords})

            # Get all active attributes associated with rule
            rule_attribute_result_set = self.Sentinel.SentinelModel.getRuleAttributes(rule_idn=rule_id, entity_active='Y')
            rule_attributes = '~'.join([eachAttr['ATTRIBUTE_VALUE'] for eachAttr in rule_attribute_result_set])
            eachRule.update({'ATTACHED_ATTRIBUTES':rule_attributes})

        # Get all criteria associated with rules
        criteria_results = self.get_rule_criteria_for_export(rule_id=rule_ids)
        # If no matching rule records found, raise error
        if not criteria_results:
            raise Exception("No associated criteria details for given rules found")

        # Get all actions associated with rules
        action_results = self.get_rule_actions_for_export(rule_id=rule_ids)
        # If no matching rule records found, raise error
        if not action_results:
            raise Exception("No associated action details for given rules found")

        excel_object_url = rule_export(self, criteria_results, action_results, rule_details)
         
        return request.RESPONSE.redirect(excel_object_url)
        
        # The below commented section to be deleted when 
        # export export functionality has been approved
        #=======================================================================
        # dtml_document = getattr(self.views, 'export_rule')
        # return dtml_document(self.views,
        #                     REQUEST=request,
        #                     rule_details=rule_details,
        #                     action_details=action_results,
        #                     criteria_details=criteria_results)
        #=======================================================================

    def get_rule_criteria_for_export(self, rule_id):
        """
        @param : rule_id - int/list - rule id

        Returns result set of criteria associated with given rules
        """
        criteria_set = self.Sentinel.SentinelModel.get_criteria_details_for_rule(rule_ids=rule_id).dictionaries()
        return criteria_set

    def get_rule_actions_for_export(self, rule_id):
        """
        @param : rule_id - int/list - rule id

        Return details of action and action parameters associated with given rule (in form of list of dictionaries)
        Each dictionary corresponds to action record.
        """
        rule_actions_record_set = self.Sentinel.SentinelModel.get_action_details_for_rule(rule_ids=rule_id)

        return self.get_action_details_for_export(actions_record_set=rule_actions_record_set)

    def showRuleSetPage(self):
        """
        @description : This method used to show rule set search page.
        @return : return rule set search page
        """
        request = self.REQUEST
        header_type = ''
        if request.has_key('header_type'):
            header_type = request['header_type']
        header = self.ZeUI.getHeader(header_type)
        footer = self.ZeUI.getFooter(header_type)
        keywords_rst = self.Sentinel.SentinelModel.getKeywords()
        I_CONTEXT_ID = request.get('I_CONTEXT_ID','')
        dtml_document = getattr(self.views, 'rule_set_search')
        next_page = header+dtml_document(self.views,
                                         REQUEST=request,
                                         keywords_rst=keywords_rst,
                                         I_CONTEXT_ID=I_CONTEXT_ID
                                         )+footer
        return next_page

    def getRulesSetResultPage(self):
        """
        @description : This method used to get rule set result page.
        @return : return to rule set result page.
        """
        request = self.REQUEST
        rule_set_title = request.get('rule_set_title','')
        event_id = request.get('event_title','')
        rule_title=request.get('rule_title','')
        package_enabled = request.get('filter_enabled','Y')
        ruleset_keyword = request.get('ruleset_keyword','')
        rule_category = request.get('rule_category','')
        package_id = request.get('package_id','')
        rule_src_idn = request.get('rule_src_idn','')
        rule_set_type=request.get('rule_set_type','')
        rules_set_execution_type=request.get('rules_set_execution_type','')
        checked_chkbox = request.get('checked_chkbox','')
        I_RULE_ATTR_IDN = request.get('I_RULE_ATTR_IDN','')
        if I_RULE_ATTR_IDN:
            attribute_value_idns = str(request.get('attribute_value_idn',[]))[1:-1]
        else:
            attribute_value_idns = ''
        noResultMsg=self.ZeUtil.getJivaMsg(msg_code='627')
        status = request.get('status','')
        if status:
            msg_code = {'activate':'017','deactivate':'016'}
            request.set('info_alert', self.ZeUtil.getJivaMsg(msg_code = msg_code[status.lower()]))
        header = self.ZeUI.getHeader()
        footer = self.ZeUI.getFooter()
        # pagination
        page_info = self.getPageDetails()

        next_count = self.Sentinel.SentinelModel.\
                   getRuleSetCount(\
                       package_enabled=package_enabled,
                       rule_set_title=rule_set_title,
                       event_id=event_id,
                       rule_category=rule_category,
                       rule_title=rule_title,
                       ruleset_keyword=ruleset_keyword,
                       attribute_value_idns=attribute_value_idns,
                       rule_set_type=rule_set_type,
                       rules_set_execution_type=rules_set_execution_type,
                       rule_src_idn=rule_src_idn
                       )[0][0]

        package_details_recordset = self.Sentinel.\
                                  SentinelModel.selectRuleSetDetails(\
                                      package_enabled=package_enabled,
                                      rule_set_title=rule_set_title,
                                      event_id=event_id,
                                      rule_title=rule_title,
                                      rule_category=rule_category,
                                      ruleset_keyword=ruleset_keyword,
                                      attribute_value_idns=attribute_value_idns,
                                      rule_set_type=rule_set_type,
                                      rules_set_execution_type=rules_set_execution_type,
                                      rule_src_idn=rule_src_idn,
                                      query_from=page_info['I_START_REC_NO'],
                                      query_to=page_info['I_END_REC_NO']
                                  )
        package_details_list = package_details_recordset.dictionaries()

        for eachpackageRecord in package_details_list:

            eventType = self.Sentinel.SentinelModel.\
                      getCodeEventDetails(\
                          eachpackageRecord['EVENT_TITLE']
                          )[0]['EVENT_DESCRIPTION']
            ruleCategory = self.Sentinel.SentinelModel.\
                         getCodeRuleCategory(\
                             eachpackageRecord['RULE_CTGY']
                             )[0]['CTGY_CD']

            eachpackageRecord['EVENT_TYPE']=eventType
            eachpackageRecord['RULE_CTGY']=ruleCategory

        current_page = request.get('export_flag','N') == 'Y'\
                     and 'export_rule_set_result_page'\
                     or 'rules_set_result_page'
        dtml_document = getattr(self.views,current_page)
        return header+dtml_document(self.views,\
                                    REQUEST=request,
                                    new_rule_set_list=package_details_list,
                                    rule_set_title=rule_set_title,
                                    event_id=event_id,
                                    rule_title=rule_title,
                                    filter_enabled = package_enabled,
                                    total_rec = next_count,
                                    I_CUR_PG=page_info['I_CUR_PAGE'],
                                    rule_category = rule_category,
                                    ruleset_keyword = ruleset_keyword,
                                    package_id=package_id,
                                    checked_chkbox=checked_chkbox,
                                    noResultMsg=noResultMsg,
                                    rule_src_idn=rule_src_idn,
                                    rule_set_type=rule_set_type,
                                    rules_set_execution_type=rules_set_execution_type
                                    )+footer

    def showRuleAttachPage(self):
        """
        @description : This method is used to show rule attach page.
        @return : return to rule set search page.
        """
        request = self.REQUEST
        I_CONTEXT_ID = request.get('I_CONTEXT_ID')
        header_type = ''
        if request.has_key('header_type'):
            header_type = request['header_type']
        header = self.ZeUI.getHeader(header_type)
        footer = self.ZeUI.getFooter(header_type)
        keywords_rst = self.Sentinel.SentinelModel.getKeywords()
        dtml_document = getattr(self.views, 'rules_search_for_ruleset')
        return header+dtml_document(self.views,
                                    REQUEST = request,
                                    keywords_rst = keywords_rst,
                                    I_CONTEXT_ID = I_CONTEXT_ID
                                    )+footer

    def showAddRuleSetPage(self):
        """
        @description : This method is used to show add rule set page.
        @return : return to rule set add page.
        """
        request = self.REQUEST
        header_type = ''
        if request.has_key('header_type'):
            header_type = request['header_type']
        header = self.ZeUI.getHeader(header_type)
        footer = self.ZeUI.getFooter(header_type)
        dtml_document = getattr(self.views, 'rule_set_add')
        next_page = header+dtml_document(self.views, REQUEST=request)+footer
        return next_page

    @normalize_form()     
    def addRuleSet(self):
        """
        @description : This method is used to add rule set.
        @return : return to rule set edit page.
        """
        request=self.REQUEST
        rule_ids=request.get('rule_ids',0)
        rule_ids=rule_ids.split(',')
        rule_source_code = request.get('rule_source_code','')
        rule_source_code = rule_source_code.split(',')
        I_CONTEXT_ID = request.get('I_CONTEXT_ID','')
        label = request.get('label','')
        if type(label) == type('string'):
            label = [label]
        # insert pkg
        rule_set_title=request.get('rule_set_title','').strip()
        rule_set_description=request.get('rule_set_description','').strip()
        rule_set_type=request.get('rule_set_type','')
        rules_set_execution_type=request.get('rules_set_execution_type','')
        rule_ctgy_id=request.get('category','')
        event_type=request.get('event_type','')
        rule_src_idn = request.get('rule_src_idn', '')
        if rule_src_idn == '':
            rule_src_idn = self.getRuleSetSource(rule_src_cd='general').dictionaries()[0]['SRC_IDN'] # if rule_src_idn is 4 then General Rule
        entity_active = 'Y'
        user_idn=self.ZeUser.Model.getLoggedinUserIdn()
        # insert in to package master
        if rule_ids.__len__() == 1: # checking Rule is attached or not
            if rule_ids[0] == '':
                return '0'
        ext_pkg_cd = 'RULESET'+get_base_external_cd(self)
        pkg_id=self.Sentinel.SentinelModel.insertRuleSet(rule_set_title,
                                                         rule_set_description,
                                                         rule_set_type,
                                                         rules_set_execution_type,
                                                         rule_ctgy_id,
                                                         event_type,
                                                         rule_src_idn,
                                                         entity_active,
                                                         user_idn,
                                                         ext_pkg_cd
                                                         )
        if pkg_id:
            pkg_id=pkg_id[0][0] # getting package id

        else:
            print "No package id.."
        # insert in to package rule
        count=0
        count_merge = 0
        for rule_id in rule_ids:
            idpool_label_idn = ''
            if rule_source_code[count]== 'idpool':
                count_merge = count_merge + 1
            else:
                label_value = label[count-count_merge]
                if label_value:
                    idpool_label_result = self.Sentinel.SentinelModel.get_idpool_label_idn(label_value)
                    if idpool_label_result.dictionaries():
                        idpool_label_idn = idpool_label_result[0][0]
            self.Sentinel.SentinelModel.insertAttachRule(\
                pkg_id,
                rule_id,
                count,
                user_idn,
                idpool_label_idn
            )
            count += 1
        return pkg_id

    def showRuleSetEditPage(self):
        """
        @description : This method is used to returns rule set update page
        @return : returns rule set update page.
        """
        request = self.REQUEST
        pkg_id = request.get('pkg_id','0')
        I_CONTEXT_ID = request.get('I_CONTEXT_ID','')
        checked_values = request.get('checked_values','')
        dtml_document = getattr(self.views, 'rule_set_edit')
        src = request.get('src','')
        msg_code = {'addRuleSet':'700','updateRuleSet':'697'}
        if src:
            request.set('info_alert', self.ZeUtil.getJivaMsg(msg_code = msg_code[src]))
        header = self.ZeUI.getHeader()
        footer = self.ZeUI.getFooter()
        next_page = header+dtml_document(self.views,\
                                         request=request,
                                         pkg_id=pkg_id,\
                                         I_CONTEXT_ID = I_CONTEXT_ID,\
                                         checked_values = checked_values
                                         )+footer
        return next_page

    def showRuleSetViewPage(self):
        """
        @description : This method is used to return rule set view page.
        @return : return rule set view page.
        """
        request = self.REQUEST
        pkg_id = request.get('pkg_id','0')
        header_type = ''
        if request.has_key('header_type'):
            header_type = request['header_type']
        header = self.ZeUI.getHeader(header_type)
        footer = self.ZeUI.getFooter(header_type)
        I_CONTEXT_ID = request.get('I_CONTEXT_ID','')
        checked_values = request.get('checked_values','')
        dtml_document = getattr(self.views, 'rule_set_view')
        next_page = header+dtml_document(self.views,\
                                         request=request,
                                         pkg_id=pkg_id,\
                                         I_CONTEXT_ID = I_CONTEXT_ID,\
                                         checked_values = checked_values
                                         )+footer
        return next_page


    def getRuleSetDetailsforId(self,pkg_id):
        """
        @description : This method is used to get rule set details based on package id.

        @param : pkg_id {int} package id
        @return : return rule set details
        """
        request = self.REQUEST
        result_set = self.Sentinel.SentinelModel.showPackageDetailsforPkgId(\
            pkg_id=pkg_id).dictionaries()
        if result_set:
            result_set[0]['PKG_TITLE'] = quote(result_set[0]['PKG_TITLE'])
            result_set[0]['PKG_DESCRIPTION'] = quote(result_set[0]['PKG_DESCRIPTION'])
        return result_set

    @normalize_form()     
    def updateRuleSet(self):
        """
        @description : This method is used to update rule set.
        @return : return to rule set edit page.
        """
        request=self.REQUEST
        msg =request.get('msg','') # Request Msg for Update
        rule_ids=request.get('rule_ids','')
        rule_ids=rule_ids.split(',') # Rules which are inserted taken from form
        rule_source_code = request.get('rule_source_code','')
        rule_source_code = rule_source_code.split(',')
        rule_set_title=request.get('rule_set_title','').strip()
        rule_set_description=request.get('rule_set_description','').strip()
        rule_set_type=request.get('rule_set_type','').strip()
        rules_set_execution_type=request.get('rules_set_execution_type','').strip()
        ruleset_id = request.get('ruleset_id','')
        I_CONTEXT_ID = request.get('I_CONTEXT_ID')
        rule_ctgy_id=request.get('category','').strip()
        label = request.get('label','')
        if type(label) == type('string'):
            label = [label]
        event_type=request.get('event_type','').strip()
        rule_src_idn = request.get('rule_src_idn', '')
        if rule_src_idn == '':
            rule_src_idn = self.getRuleSetSource(rule_src_cd='general').dictionaries()[0]['SRC_IDN']
        pkg_id=request.get('pkg_id','').strip()
        user_idn=self.ZeUser.Model.getLoggedinUserIdn()
        self.Sentinel.SentinelModel.updateRuleSet(\
            rule_set_title,
            rule_set_description,
            rule_set_type,
            rules_set_execution_type,
            rule_ctgy_id,
            event_type,
            rule_src_idn,
            user_idn,
            pkg_id
        )
        self.Sentinel.SentinelModel.InactiveRulePkg(pkg_id)
        count = 0
        count_merge = 0
        for rule_id in rule_ids:
            idpool_label_idn = ''
            if rule_source_code[count] == 'idpool':
                count_merge = count_merge + 1
            else:
                label_value = label[count-count_merge]
                if label_value:
                    idpool_label_result = self.Sentinel.SentinelModel.get_idpool_label_idn(label_value)
                    if idpool_label_result.dictionaries():
                        idpool_label_idn = idpool_label_result[0][0]
            self.Sentinel.SentinelModel.insertAttachRule(\
                pkg_id,
                rule_id,
                count,
                user_idn,
                idpool_label_idn
            )
            count += 1
        request.set('src','updateRuleSet')
        return self.showRuleSetEditPage()

    security.declareProtected('Ze Sentinel ViewExportRuleSet', 'showExportRuleSetSearchPage')
    def showExportRuleSetSearchPage(self):
        """
        @description : This method is used to show export rule set search page.
        @return : returns to export rule set search page.
        """
        request = self.REQUEST
        header = self.ZeUI.getHeader()
        footer = self.ZeUI.getFooter()
        keywords_rst = self.Sentinel.SentinelModel.getKeywords()
        dtml_document = getattr(self.views, 'export_rule_set_search')
        next_page = header+dtml_document(self.views, REQUEST=request,keywords_rst=keywords_rst)+footer
        return next_page

    def showRuleSetExportToXlPage(self):
        """
        This method returns DTML page with content type set as application ms excel.
        DTML page contains all data related to rule sets selected for export.
        """
        request = self.REQUEST

        pkg_id = request.get('cid','')
        rule_set_title = request.get('rule_set_title','')
        event_id = request.get('event_id','')
        rule_title=request.get('rule_title','')
        package_enabled = request.get('filter_enabled','Y')
        associated_rules = set([])

        ruleset_result_set = self.Sentinel.SentinelModel.showPackageDetailsforPkgId(pkg_id=pkg_id,
                                                                                    rule_set_title=rule_set_title,
                                                                                    event_id=event_id,
                                                                                    rule_title=rule_title,
                                                                                    package_enabled=package_enabled
                                                                                    )
        ruleset_details = ruleset_result_set.dictionaries()
        # If no matching rule records found, raise error
        if not ruleset_details:
            raise Exception("No rule set details found")

        for each_rule_set in ruleset_details:
            # Get all active keywords associated with rule set
            rule_set_id = each_rule_set['PKG_ID']
            rule_set_keywords_result_set = self.Sentinel.SentinelModel.getRuleSetKeywords(rule_set_id=rule_set_id,
                                                                                          entity_active='Y')
            rule_set_keywords = '~'.join([each_kw['KEYWORD_DESC'] for each_kw in rule_set_keywords_result_set])
            each_rule_set.update({'RULESET_KEYWORD_DESC':rule_set_keywords})

            # Get all active attributes associated with rule set
            rule_set_attributes_result_set = self.Sentinel.SentinelModel.getRuleSetAttributes(pkg_id=rule_set_id,
                                                                                              entity_active='Y')
            rule_set_attributes = '~'.join([eachAttr['ATTRIBUTE_VALUE'] for eachAttr in rule_set_attributes_result_set])
            each_rule_set.update({'RULESET_ATTACHED_ATTRIBUTES':rule_set_attributes})

            # Get all active rules associated with rule set
            rules_result_set = self.Sentinel.SentinelModel.showRuleDetailsForPackageId(pkg_id=rule_set_id,
                                                                                       entity_active='Y')
            associated_rules.update([each_rule['SRE_RULE_IDN'] for each_rule in rules_result_set])

        criteria_results = self.get_rule_criteria_for_export(rule_id=list(associated_rules))
        # If no matching rule records found, raise error
        if not criteria_results:
            raise Exception("No associated criteria details for given rule set found")

        action_results = self.get_rule_actions_for_export(rule_id=list(associated_rules))
        # If no matching rule records found, raise error
        if not action_results:
            raise Exception("No associated action details for given rule set found")

        excel_object_url = rule_set_export(self, criteria_results, action_results, ruleset_details)
        
        return request.RESPONSE.redirect(excel_object_url)
        
        # The below commented section to be deleted when 
        # export export functionality has been approved
        #===============================================================================
        # # Set mime type for DTML document
        # stylestr = self.Reports.Controller.getExcelStyleSheet(view_name='sentinel_rule_set_export.xls')
        # 
        # dtml_document = getattr(self.views, 'export_rule_set')
        # return stylestr + dtml_document(self.views,
        #                                 REQUEST=request,
        #                                 ruleset_details=ruleset_details,
        #                                 criteria_results=criteria_results,
        #                                 action_results=action_results)
        #===============================================================================

    def getRuleDetailsforPkgId(self,pkg_id,entity_active):
        """
        @description : This method is used to get rule detail for based on package id

        @param : pkg_id {int} package id.
        @param : entity_active {string} entity active either 'Y/N'
        @return : return rule set details.
        """
        request = self.REQUEST
        result_set = self.Sentinel.SentinelModel.showRuleDetailsForPackageId(pkg_id,entity_active).dictionaries()
        for each_res in result_set:
            keywords_desc = self.Sentinel.SentinelModel.getRuleKeywords(rule_id = each_res['SRE_RULE_IDN'],
                                                                        entity_active='Y')
            kw_dsc = [each_kw['KEYWORD_DESC'] for each_kw in keywords_desc]
            keyword_desc = '@@'.join(kw_dsc)
            each_res.update({'RULE_KEYWORD_DESC':keyword_desc})

            # Get attached active attributes
            attached_attributes_result_set = self.Sentinel.SentinelModel.getRuleAttributes(rule_idn=each_res['SRE_RULE_IDN'], entity_active='Y')
            attached_attributes_str = '~'.join([eachAttr['ATTRIBUTE_VALUE'] for eachAttr in attached_attributes_result_set])
            each_res.update({'RULE_ATTACHED_ATTRIBUTES':attached_attributes_str})

        return result_set

    def getRuleActions(self, ruleId):
        """
        @param: ruleId - int - rule id

        Returns actions details for given rule id
        """

        return self.Sentinel.SentinelModel.get_rule_actions(rule_id=ruleId).dictionaries()

    def getRuleCriteriaString(self, rule_id):
        """
        @param: rule_id - int - rule id

        Returns criteria details for given rule id
        """
        rs = self.Sentinel.SentinelModel.getCriteriasForRule(rule_id)
        return rs.dictionaries()

    security.declareProtected('Ze Sentinel ViewImportRule', 'showImportRulePage')
    def showImportRulePage(self):
        """
        @description : This method is used to show import rule page
        @return : return to show import rule page
        """
        request = self.REQUEST
        header_type = ''
        if request.has_key('header_type'):
            header_type = request['header_type']
        header = self.ZeUI.getHeader(header_type)
        footer = self.ZeUI.getFooter(header_type)
        dtml_document = getattr(self.views, 'import_rule_page')
        return header+dtml_document(self.views, REQUEST=request)+footer

    def importConfiguration(self):
        """
        @description : This method is used to import configuration.
        @return : calls a method in sentinel install file to rule the install script
        based on import type passed.
        """
        request = self.REQUEST
        import_type = request.get('import_tab').strip()
        import_name=request['import_file'].filename
        filename = import_name.split('\\')[-1]

        if request['import_file']:
            cwd = os.path.abspath(os.path.dirname(__file__))
            if not os.path.exists(cwd+'/install_rule_scripts'):
                os.mkdir(cwd+'/install_rule_scripts')

            install_script_path = os.path.join(cwd,\
                                               'install_rule_scripts',
                                               filename
                                               )
            raw_file = request['import_file'].read()
            f = file(install_script_path, 'wb')
            f.write(raw_file)                   # write text to file
            f.close()
            
            if not os.path.isfile(install_script_path):
                err_msg = 'Unable to %s :: "%s" is not a valid filename' % (import_type, install_script_path)
                return err_msg
        
            if import_type == 'Import Rule':
                return self.importSentinelRules(filename = filename)
            elif import_type == 'action':
                return self.importSentinelActions(filename = filename)
            elif import_type == 'Import Rule Set':
                return self.importSentinelPackageRules(filename = filename)
            else:
                return self.importSentinelAssessmentRuleset(filename = filename)

    security.declareProtected('Ze Sentinel ViewImportRuleSet', 'showImportRuleSetPage')
    def showImportRuleSetPage(self):
        """
        @description : This method is used to show import rule set page.
        @return : return to show import rule set page
        """
        request = self.REQUEST
        header_type = ''
        if request.has_key('header_type'):
            header_type = request['header_type']
        header = self.ZeUI.getHeader(header_type)
        footer = self.ZeUI.getFooter(header_type)
        dtml_document = getattr(self.views, 'import_rule_set_page')
        return header+dtml_document(self.views, REQUEST=request)+footer

    def showRuleAddPage(self):
        """
        @description : This method is used to show rule add page.
        @return : return to rule add page.
        """
        request = self.REQUEST
        output_entity = constants.OUTPUT_ENTITY
        I_CONTEXT_ID = request.get('I_CONTEXT_ID','')
        dtml_document = getattr(self.views, 'rules_add_page')
        header = self.ZeUI.getHeader('Add Rule')
        footer = self.ZeUI.getFooter()
        next_page = header+dtml_document(self.views,
                                         request=request,
                                         I_CONTEXT_ID = I_CONTEXT_ID,
                                         output_entity = output_entity)+footer
        return next_page

    def getRuleElifDetails(self):
        """
        @description : This method is used to fill rule elif contents in the respective block
        @return : return to rule else if page.
        """
        request = self.REQUEST
        tabCount = {True: request.get('elifblkcount', ''), False: request.get('tab_count', '')}\
                            [request.get('tab_count', '') == '']
        I_CONTEXT_ID = request.get('I_CONTEXT_ID', '')
        form_name = request.get('form_name', '')
        delete_count = int(request.get('delete_count', ''))
        header_type = ''
        if request.has_key('header_type'):
            header_type = request['header_type']
        header = self.ZeUI.getHeader(header_type)
        footer = self.ZeUI.getFooter(header_type)
        dtml_document = getattr(self.views, 'rule_elseif_page')
        return header+dtml_document(self.views, REQUEST=request,
                             tabCount=tabCount,
                             form_name=form_name,
                             I_CONTEXT_ID=I_CONTEXT_ID)+footer

    def showCriteria(self):
        """
        @description : This method is used to show criteria attach page.
        @return : returns criteria attach page.
        """
        request = self.REQUEST
        criteriatype = self.getCriteriaType()
        ruletype = constants.RULE_TYPE
        rule_type = request.get('rule_type','')
        tab_count = request.get('tabCount','')
        header_type = ''
        if request.has_key('header_type'):
            header_type = request['header_type']
        header = self.ZeUI.getHeader(header_type)
        footer = self.ZeUI.getFooter(header_type)
        dec_table_id = request.get('dec_table_id', '')
        I_CONTEXT_ID = request.get('I_CONTEXT_ID','')
        dtml_document = getattr(self.views, 'criteria_attach')
        return header+dtml_document(self.views, 
                                    REQUEST=request,
                                    tabCount=tab_count,
                                    dec_table_id=dec_table_id,
                                    I_CONTEXT_ID =I_CONTEXT_ID,
                                    criteriatype=criteriatype,
                                    ruletype=ruletype)+footer

    def getCriteriaFilterPage(self):
        """
        @description : This method is used to get criteria filter page.
        @return : return to criteria filter page.
        """
        request = self.REQUEST
        criteria_name = self.ZeUtil.replaceQuotes(request.get('criteria_title','').strip())
        criteria_id = request.get('criteria_id','')
        criteria_reftable = request.get('criteria_reftable','')
        entity = request.get('entity','').strip()
        attached_criteria = request.get('attached_criteria','')
        entity_attribute = request.get('entity_attribute','').strip()
        dec_table_id = request.get('dec_table_id', '')
        rule_type = request.get('Rule type', '')
        criteria_type = request.get('criteria_type', '')

        header = self.ZeUI.getHeader()
        footer = self.ZeUI.getFooter()
        # pagination
        page_info = self.getPageDetails()
        noResultMsg=self.ZeUtil.getJivaMsg(msg_code='627')
        next_count = self.Sentinel.SentinelModel.selectCriteriaDetailsCount(criteria_id=criteria_id,
                                                                            criteria_name=criteria_name,
                                                                            entity = entity,
                                                                            rule_type = rule_type,
                                                                            criteria_type = criteria_type,
                                                                            criteria_reftable = criteria_reftable,
                                                                            dec_table_id=dec_table_id,
                                                                            entity_attribute = entity_attribute)[0][0]

        new_criteria_recordset = self.Sentinel.SentinelModel.selectCriteriaDetails(criteria_id=criteria_id,
                                                                                   criteria_name=criteria_name,
                                                                                   entity = entity,
                                                                                   rule_type = rule_type,
                                                                                   criteria_type = criteria_type,
                                                                                   entity_attribute = entity_attribute,
                                                                                   criteria_reftable = criteria_reftable,
                                                                                   dec_table_id=dec_table_id,
                                                                                   query_from=page_info['I_START_REC_NO'],
                                                                                   query_to=page_info['I_END_REC_NO'])
        new_criteria_list = new_criteria_recordset.dictionaries()
        noResultMsg=self.ZeUtil.getJivaMsg(msg_code='627')

        dtml_document = getattr(self.views,'criteria_filter_page')
        return header+dtml_document(\
            self.views,
            REQUEST=request,
            new_criteria_list=new_criteria_list,
            criteria_id = criteria_id,
            total_rec=next_count,
            I_CUR_PG=page_info['I_CUR_PAGE'],
            criteria_title=criteria_name,
            entity=entity,
            entity_attribute=entity_attribute,
            rule_type = rule_type,
            criteria_type = criteria_type,
            noResultMsg=noResultMsg,
            criteria_reftable=criteria_reftable,
            attached_criteria=attached_criteria,
            dec_table_id = dec_table_id
            )+footer

    def getActionFilterPage(self):
        """
        @description : This method is used to get action filter page.
        @return : return to action filter page.
        """
        request = self.REQUEST
        action_script = request.get('action_script','')
        action_title = self.ZeUtil.replaceQuotes(request.get('action_title','').strip())
        noResultMsg=self.ZeUtil.getJivaMsg(msg_code='627')
        attached_action = request.get('attached_action','')
        tabCount = request.get('tabCount','')
        pop_up = request.get('pop_up','')
        I_CONTEXT_ID = request.get('I_CONTEXT_ID','')
        # pagination
        page_info = self.getPageDetails()

        total_count = self.Sentinel.SentinelModel.\
                    selectDetailedActionsCount(
                        action_script=action_script,
                        action_title=action_title
                    )

        action_details_list = self.Sentinel.SentinelModel.\
                            selectDetailedActions(
                                action_script=action_script,
                                action_title=action_title,
                                query_from=page_info['I_START_REC_NO'],
                                query_to=page_info['I_END_REC_NO']
                                ).dictionaries()

        for actionid in action_details_list:
            actionid['ACTION_ID'] = actionid['IDN']
            param_list = []
            param_set = self.Sentinel.SentinelModel.selectActionParams(action_idn = actionid['IDN']).dictionaries()
            if param_set:
                for param in param_set:
                    if param['PARAM_NAME'] and param['PARAM_VALUE']:
                        param_list.append('%s=%s' % (param['PARAM_NAME'], param['PARAM_VALUE']))
                actionid['parameter_details'] = param_list
            else:
                actionid['parameter_details'] = []
        dtml_document = getattr(self.views, 'action_filter_page')
        return dtml_document(self.views, REQUEST=request,
                             attached_action=attached_action,
                             action_script=action_script,
                             action_title=action_title,
                             action_details_list=action_details_list,
                             tabCount=tabCount,
                             pop_up=pop_up,
                             total_rec=len(total_count),
                             I_CUR_PG=page_info['I_CUR_PAGE'],
                             I_CONTEXT_ID = I_CONTEXT_ID,
                             noResultMsg=noResultMsg
                             )

    def showRuleUpdatePage(self):
        """
        @description : This method is used to show rule edit page.
        @return : return to show rule edit page.
        """
        request = self.REQUEST
        rule_id = request.get('rule_id','')
        I_CONTEXT_ID = request.get('I_CONTEXT_ID','')
        entity_active = request.get('entity_active','')
        src = request.get('src','')
        pkg_flag = request.get('pkg_flag','N')
        pkg_context_id = request.get('pkg_context_id','')
        rule_src_idn = request.get('rule_src_idn', 0)
        msg_code = {'copyRule':'699','addRule':'436','updateRule':'437', 'addDecRule':'436'}
        dec_table_id = ''
        if src:
            request.set('info_alert', self.ZeUtil.getJivaMsg(msg_code = msg_code[src]))
        output_entity = constants.OUTPUT_ENTITY
        header = self.ZeUI.getHeader()
        footer = self.ZeUI.getFooter()
        result_set = self.Sentinel.SentinelModel.selectRuleValuesByTitle(\
            rule_id=rule_id).dictionaries()
        if result_set:
            result_set[0]['TITLE'] = quote(result_set[0]['TITLE'])
            result_set[0]['DESCRIPTION'] = quote(result_set[0]['DESCRIPTION'])
        criteriaaction_set,criteria_count,action_count = self.\
                          getRuleActionCriteriaDetails(rule_id=rule_id)
        for i in range(0, len(criteriaaction_set[0])):
            if criteriaaction_set[0][i]['type'] == 'criteria':
                dec_table_id = criteriaaction_set[0][i]['DEC_ID']
        if dec_table_id:
            dtml_document = getattr(self.views, 'dec_rules_edit_page')
        elif int(rule_src_idn) == 1:
            dtml_document = getattr(self.views, 'validation_rule_update_page')
        else:
            dtml_document = getattr(self.views, 'rules_update_page')
        next_page = header+dtml_document(self.views,
                                         request=request,
                                         rule_id=rule_id,
                                         result_set=result_set,
                                         dec_table_id=dec_table_id,
                                         criteriaaction_set=criteriaaction_set,
                                         criteria_count = criteria_count,
                                         action_count = action_count,
                                         I_CONTEXT_ID=I_CONTEXT_ID,
                                         src=src,
                                         entity_active=entity_active,
                                         pkg_flag=pkg_flag,
                                         pkg_context_id=pkg_context_id,
                                         output_entity = output_entity,
                                         rule_src_idn=rule_src_idn)+footer
        return next_page

    def showRuleViewPage(self):
        """
        @description : This method is used to show rule view page
        @return : return to show rule view page
        """
        request = self.REQUEST
        rule_id = request.get('rule_id','')
        I_CONTEXT_ID = request.get('I_CONTEXT_ID','')
        entity_active = request.get('entity_active','')
        output_entity = constants.OUTPUT_ENTITY
        header = self.ZeUI.getHeader()
        footer = self.ZeUI.getFooter()
        result_set = self.Sentinel.SentinelModel.selectRuleValuesByTitle(\
            rule_id=rule_id).dictionaries()
        if result_set:
            result_set[0]['TITLE'] = quote(result_set[0]['TITLE'])
            result_set[0]['DESCRIPTION'] = quote(result_set[0]['DESCRIPTION'])
        criteriaaction_set,criteria_count,action_count = self.\
                          getRuleActionCriteriaDetails(rule_id=rule_id)
        dtml_document = getattr(self.views, 'rule_view')
        next_page = header+dtml_document(self.views,
                                         request=request,
                                         rule_id=rule_id,
                                         result_set=result_set,
                                         criteriaaction_set=criteriaaction_set,
                                         criteria_count = criteria_count,
                                         action_count = action_count,
                                         I_CONTEXT_ID=I_CONTEXT_ID,
                                         entity_active=entity_active,
                                         output_entity = output_entity)+footer
        return next_page

    def validate_output_label(self, rule_idn=''):
        """
        This method is used to validate rule that
        it does not have same out label used in another rule
        """
        request = self.REQUEST
        selected_label = request.get('label','')
        selected_rule_type = request.get('rule_type','')
        labels = []
        if selected_rule_type == 'Identification':
            label_results = self.Sentinel.SentinelModel.is_label_in_use(selected_label,rule_idn=rule_idn).dictionaries()
            if (label_results) or (selected_label==''):
                request.set('error_alert', self.ZeUtil.getJivaMsg(msg_code='V201305292022'))
                return 0
        return 1

    @normalize_form() 
    def addRule(self):
        """
        @description : This method is used to add rule
        @return : This method returns Rule edit Page after adding a new rule
        """
        request = self.REQUEST
        if not self.validate_output_label():
            return self.ZeUI.getInfoAlertSlot()
        try:
            user_id = int(self.cms.ZeUser.Model.getLoggedinUserIdn())
        except:
            user_id = 3
        rule_title = request.get('rule_title','').strip()
        business_process = request.get('business_process','')
        rule_type = request.get('rule_type','')
        rule_execution_type = request.get('rule_execution_type','')
        rule_description = request.get('rule_description','').strip()
        event_cd = request.get('event_title','')
        output_entity = request.get('output_entity','')
        rule_output_label = request.get('label','')
        dec_table_id = request.get('dec_table_id', '')
        rule_src_idn = request.get('rule_src_idn', '')
        flowchart_doc = request.get('flowchart_doc', '')
        if flowchart_doc:
            fname=r"flowchart_%s" % str(flowchart_doc.filename)
            fax_file_name = fname.split('\\')[-1]
            raw_file = flowchart_doc.read() ## uploaded file data reading
            current_id = self.Document.Model.zsqls.getEnclosureID()        #ZC_Fix: move this to model
            next_id = int(current_id[0]['current_idn']) + 1
            try:
                fname = str(next_id) + "_" + fax_file_name
            except TypeError:
                fname = '0_' + fname
            cms = self.getPhysicalRoot().cms
            extblob = cms.sentinelUploads
            extblob.manage_addProduct['ExtBlob'].manage_addExtBlob( id=fname,
                                                                    title=fname,
                                                                    file=flowchart_doc,
                                                                    content_type='',
                                                                    permission_check=0)
        else:
            fname = ''
        ext_rule_cd = 'RULE'+get_base_external_cd(self)
        rule_id_recordset = self.Sentinel.SentinelModel.insertRuleDetails(title=rule_title,\
                                                                          business_process=business_process,\
                                                                          rule_type=rule_type,\
                                                                          rule_execution_type=rule_execution_type,\
                                                                          output_entity=output_entity,\
                                                                          rule_output_label=rule_output_label,\
                                                                          rule_description=rule_description,\
                                                                          user_id=user_id,\
                                                                          event_cd=event_cd,
                                                                          rule_doc = fname,
                                                                          rule_src_idn=rule_src_idn,
                                                                          ext_rule_cd=ext_rule_cd)

        rule_id_dictionary = rule_id_recordset.dictionaries()[0]
        rule_id = rule_id_dictionary['SRE_RULE_IDN']
        request.set('rule_id',rule_id)
        request.set('I_CONTEXT_ID','editrule_'+str(rule_id))
        request.set('src','addRule')
        action_total_count = request.get('action_total_count',0)
        criteria_total_count = request.get('criteria_total_count',0)
        
        group_count = 0
        for i in range(int(criteria_total_count)):
            if request.get('criteria_id'+str(i)):
                exec_group = request.get('criteria_exec_group'+str(i),'')
                criteria_id = request.get('criteria_id'+str(i),'')
                prefix_op = request.get('prefix_op'+str(i),'')
                suffix_op = request.get('suffix_op'+str(i),'')
                if isinstance(exec_group,str):
                    self.Sentinel.SentinelModel.addCriteriasForRule(rule_id=rule_id,
                                                                prefix_op=prefix_op.strip(),
                                                                suffix_op=suffix_op.strip(),
                                                                criteria_ids=int(criteria_id.strip()),
                                                                priority=0,
                                                                user_id=user_id,
                                                                exec_group=group_count
                                                                )
                    group_count = group_count + 1
                    
                if isinstance(exec_group,list):
                    for val in xrange(len(exec_group)):
                        self.Sentinel.SentinelModel.addCriteriasForRule(rule_id=rule_id,
                                                                prefix_op=prefix_op[val].strip(),
                                                                suffix_op=suffix_op[val].strip(),
                                                                criteria_ids=int(criteria_id[val].strip()),
                                                                priority=val,
                                                                user_id=user_id,
                                                                exec_group=group_count
                                                                )
                    group_count = group_count + 1

        # To get Max of Exec Group - For Else Block
        group_count = 0
        for i in range(int(action_total_count)):
            if request.get('action_id'+str(i)):
                exec_group = request.get('action_exec_group'+str(i),'')
                action_id = request.get('action_id'+str(i),'')
                if isinstance(exec_group,str):
                    self.Sentinel.SentinelModel.insertRuleAction(rule_id=rule_id,
                                                             action_id=int(action_id.strip()),
                                                             user_id=user_id,
                                                             priority=0,
                                                             exec_group=group_count
                                                             )
                    group_count = group_count + 1
                    
                if isinstance(exec_group,list):
                    for val in xrange(len(exec_group)):
                        self.Sentinel.SentinelModel.insertRuleAction(rule_id=rule_id,
                                                             action_id=int(action_id[val].strip()),
                                                             user_id=user_id,
                                                             priority=val,
                                                             exec_group=group_count
                                                             )
                    group_count = group_count + 1
                    
        if request.has_key('action_exec_group'):
            exec_group = request.get('action_exec_group','')
            action_id = request.get('action_id','')
            if isinstance(exec_group,str):
                self.Sentinel.SentinelModel.insertRuleAction(rule_id=rule_id,
                                                         action_id=int(action_id.strip()),
                                                         user_id=user_id,
                                                         priority=0,
                                                         exec_group=group_count
                                                         )
                    
            if isinstance(exec_group,list):
                for val in xrange(len(exec_group)):
                    self.Sentinel.SentinelModel.insertRuleAction(rule_id=rule_id,
                                                         action_id=int(action_id[val].strip()),
                                                         user_id=user_id,
                                                         priority=val,
                                                         exec_group=group_count
                                                         )
        return self.showRuleUpdatePage()
    
    @normalize_form() 
    def addDecisionTblRule(self):
        """
        @description : This method is used to add rule
        @return : This method returns Rule edit Page after adding a new rule
        """
        request = self.REQUEST
        try:
            user_id = int(self.cms.ZeUser.Model.getLoggedinUserIdn())
        except:
            user_id = 3
        rule_title = request.get('rule_title','').strip()
        business_process = request.get('business_process','')
        rule_type = request.get('rule_type','')
        rule_execution_type = request.get('rule_execution_type','')
        rule_description = request.get('rule_description','').strip()
        event_cd = request.get('event_title','')
        output_entity = request.get('output_entity','')
        rule_output_label = request.get('label','')
        dec_table_id = request.get('dec_table_id', '')
        rule_src_idn = request.get('rule_src_idn', '')
        flowchart_doc = request.get('flowchart_doc', '')
        if flowchart_doc:
            fname=r"flowchart_%s" % str(flowchart_doc.filename)
            fax_file_name = fname.split('\\')[-1]
            raw_file = flowchart_doc.read() ## uploaded file data reading
            current_id = self.Document.Model.zsqls.getEnclosureID()        #ZC_Fix: move this to model
            next_id = int(current_id[0]['current_idn']) + 1
            try:
                fname = str(next_id) + "_" + fax_file_name
            except TypeError:
                fname = '0_' + fname
            cms = self.getPhysicalRoot().cms
            extblob = cms.sentinelUploads
            extblob.manage_addProduct['ExtBlob'].manage_addExtBlob( id=fname,
                                                                    title=fname,
                                                                    file=flowchart_doc,
                                                                    content_type='',
                                                                    permission_check=0)
        else:
            fname = ''

        ext_rule_cd = 'RULE'+get_base_external_cd(self)
        rule_id_recordset = self.Sentinel.SentinelModel.insertRuleDetails(title=rule_title,\
                                                                          business_process=business_process,\
                                                                          rule_type=rule_type,\
                                                                          rule_execution_type=rule_execution_type,
                                                                          output_entity=output_entity,\
                                                                          rule_output_label=rule_output_label,\
                                                                          rule_description=rule_description,\
                                                                          user_id=user_id,\
                                                                          event_cd=event_cd,
                                                                          rule_doc = fname,
                                                                          rule_src_idn=rule_src_idn,
                                                                          ext_rule_cd=ext_rule_cd)

        rule_id_dictionary = rule_id_recordset.dictionaries()[0]
        rule_id = rule_id_dictionary['SRE_RULE_IDN']
        request.set('rule_id',rule_id)
        request.set('I_CONTEXT_ID','editrule_'+str(rule_id))
        request.set('src','addDecRule')
        ex_group_list = []
        action_total_count = request.get('action_total_count',0)
        criteria_total_count = request.get('criteria_total_count',0)
        
        group_count = 0
        for i in range(int(criteria_total_count)):
            if request.get('criteria_id'+str(i)):
                exec_group = request.get('criteria_exec_group'+str(i),'')
                criteria_id = request.get('criteria_id'+str(i),'')
                prefix_op = request.get('prefix_op'+str(i),'')
                suffix_op = request.get('suffix_op'+str(i),'')
                if isinstance(exec_group,str):
                    self.Sentinel.SentinelModel.addCriteriasForRule(rule_id=rule_id,
                                                                prefix_op=prefix_op.strip(),
                                                                suffix_op=suffix_op.strip(),
                                                                criteria_ids=int(criteria_id.strip()),
                                                                priority=0,
                                                                user_id=user_id,
                                                                exec_group=group_count
                                                                )
                    group_count = group_count + 1
                    
                if isinstance(exec_group,list):
                    for val in xrange(len(exec_group)):
                        self.Sentinel.SentinelModel.addCriteriasForRule(rule_id=rule_id,
                                                                prefix_op=prefix_op[val].strip(),
                                                                suffix_op=suffix_op[val].strip(),
                                                                criteria_ids=int(criteria_id[val].strip()),
                                                                priority=val,
                                                                user_id=user_id,
                                                                exec_group=group_count
                                                                )
                    group_count = group_count + 1

        # To get Max of Exec Group - For Else Block
        group_count = 0
        for i in range(int(action_total_count)):
            if request.get('action_id'+str(i)):
                exec_group = request.get('action_exec_group'+str(i),'')
                action_id = request.get('action_id'+str(i),'')
                if isinstance(exec_group,str):
                    self.Sentinel.SentinelModel.insertRuleAction(rule_id=rule_id,
                                                             action_id=int(action_id.strip()),
                                                             user_id=user_id,
                                                             priority=0,
                                                             exec_group=group_count
                                                             )
                    group_count = group_count + 1
                    
                if isinstance(exec_group,list):
                    for val in xrange(len(exec_group)):
                        self.Sentinel.SentinelModel.insertRuleAction(rule_id=rule_id,
                                                             action_id=int(action_id[val].strip()),
                                                             user_id=user_id,
                                                             priority=val,
                                                             exec_group=group_count
                                                             )
                    group_count = group_count + 1
                    
        if request.has_key('action_exec_group'):
            exec_group = request.get('action_exec_group','')
            action_id = request.get('action_id','')
            if isinstance(exec_group,str):
                self.Sentinel.SentinelModel.insertRuleAction(rule_id=rule_id,
                                                         action_id=int(action_id.strip()),
                                                         user_id=user_id,
                                                         priority=0,
                                                         exec_group=group_count
                                                         )
                    
            if isinstance(exec_group,list):
                for val in xrange(len(exec_group)):
                    self.Sentinel.SentinelModel.insertRuleAction(rule_id=rule_id,
                                                         action_id=int(action_id[val].strip()),
                                                         user_id=user_id,
                                                         priority=val,
                                                         exec_group=group_count
                                                         )
        return self.showRuleUpdatePage()

    @normalize_form()     
    def updateRule(self):
        """
        @description : This method is used to update rule
        @return : This method return Rule edit Page after updating rule
        """
        request = self.REQUEST
        if request.get('src')=='copyRule':
            return self.addRule()
        try:
            user_id = int(self.cms.ZeUser.Model.getLoggedinUserIdn())
        except:
            user_id = 3
        rule_id = request.get('rule_id','')
        if not self.validate_output_label(rule_idn=rule_id):
            return self.ZeUI.getInfoAlertSlot()
        rule_title = request.get('rule_title','').strip()
        event_cd = request.get('event_title','')
        rule_type = request.get('rule_type','')
        rule_execution_type = request.get('rule_execution_type','')
        rule_src_idn = request.get('rule_src_idn', '')
        rule_category = request.get('business_process','')
        description = request.get('rule_description','').strip()
        rule_keyword = request.get('rule_keyword','')
        output_entity = request.get('output_entity','')
        rule_output_label = request.get('label','')
        fname = request.get('flowchart_name','')
        dec_table_id = request.get('dec_table_id', '')
        flowchart_doc = request.get('flowchart_doc', '')
        if flowchart_doc:
            if request['flowchart_doc'] != '':
                fname=r"flowchart_%s" % str(flowchart_doc.filename)
                fax_file_name = fname.split('\\')[-1]
                raw_file = flowchart_doc.read() ## uploaded file data reading
                current_id = self.Document.Model.zsqls.getEnclosureID()        #ZC_Fix: move this to model
                next_id = int(current_id[0]['current_idn']) + 1
                try:
                    fname = str(next_id) + "_" + fax_file_name
                except TypeError:
                    fname = '0_' + fax_file_name
                cms = self.getPhysicalRoot().cms
                extblob = cms.sentinelUploads
                extblob.manage_addProduct['ExtBlob'].manage_addExtBlob(
                    id=fname,
                    title=fname,
                    file=flowchart_doc,
                    content_type='',
                    permission_check=0)

        self.Sentinel.SentinelModel.updateRuleDetails(id=rule_id,
                                                      title=rule_title,
                                                      rule_category=rule_category,
                                                      rule_type=rule_type,
                                                      rule_execution_type=rule_execution_type,
                                                      event_cd=event_cd,
                                                      description=description,
                                                      rule_keyword = rule_keyword,
                                                      output_entity = output_entity,
                                                      rule_output_label = rule_output_label,
                                                      user_id=user_id,
                                                      rule_doc=fname,
                                                      rule_src_idn=rule_src_idn)


        self.Sentinel.SentinelModel.deActivateAllActionsForRule(rule_id=rule_id)
        self.Sentinel.SentinelModel.deActivateAllCriteriaForRule(rule_id=rule_id)

        action_total_count = request.get('action_total_count',0).strip()
        criteria_total_count = request.get('criteria_total_count',0).strip()
        group_count = 0
        for i in range(int(criteria_total_count)):
            if request.get('criteria_id'+str(i)):
                exec_group = request.get('criteria_exec_group'+str(i),'')
                criteria_id = request.get('criteria_id'+str(i),'')
                prefix_op = request.get('prefix_op'+str(i),'')
                suffix_op = request.get('suffix_op'+str(i),'')
                if isinstance(exec_group,str):
                    self.Sentinel.SentinelModel.addCriteriasForRule(rule_id=rule_id,
                                                                prefix_op=prefix_op.strip(),
                                                                suffix_op=suffix_op.strip(),
                                                                criteria_ids=int(criteria_id.strip()),
                                                                priority=0,
                                                                user_id=user_id,
                                                                exec_group=group_count
                                                                )
                    group_count = group_count + 1
                    
                if isinstance(exec_group,list):
                    for val in xrange(len(exec_group)):
                        self.Sentinel.SentinelModel.addCriteriasForRule(rule_id=rule_id,
                                                                prefix_op=prefix_op[val].strip(),
                                                                suffix_op=suffix_op[val].strip(),
                                                                criteria_ids=int(criteria_id[val].strip()),
                                                                priority=val,
                                                                user_id=user_id,
                                                                exec_group=group_count
                                                                )
                    group_count = group_count + 1

        # To get Max of Exec Group - For Else Block
        group_count = 0
        for i in range(int(action_total_count)):
            if request.get('action_id'+str(i)):
                exec_group = request.get('action_exec_group'+str(i),'')
                action_id = request.get('action_id'+str(i),'')
                if isinstance(exec_group,str):
                    self.Sentinel.SentinelModel.insertRuleAction(rule_id=rule_id,
                                                             action_id=int(action_id.strip()),
                                                             user_id=user_id,
                                                             priority=0,
                                                             exec_group=group_count
                                                             )
                    group_count = group_count + 1
                    
                if isinstance(exec_group,list):
                    for val in xrange(len(exec_group)):
                        self.Sentinel.SentinelModel.insertRuleAction(rule_id=rule_id,
                                                             action_id=int(action_id[val].strip()),
                                                             user_id=user_id,
                                                             priority=val,
                                                             exec_group=group_count
                                                             )
                    group_count = group_count + 1
                    
        if request.has_key('action_exec_group'):
            exec_group = request.get('action_exec_group','')
            action_id = request.get('action_id','')
            if isinstance(exec_group,str):
                self.Sentinel.SentinelModel.insertRuleAction(rule_id=rule_id,
                                                         action_id=int(action_id.strip()),
                                                         user_id=user_id,
                                                         priority=0,
                                                         exec_group=group_count
                                                         )
                    
            if isinstance(exec_group,list):
                for val in xrange(len(exec_group)):
                    self.Sentinel.SentinelModel.insertRuleAction(rule_id=rule_id,
                                                         action_id=int(action_id[val].strip()),
                                                         user_id=user_id,
                                                         priority=val,
                                                         exec_group=group_count
                                                         )

        if request.get('src','') == '':
            request.set('src','updateRule')
        return self.showRuleUpdatePage()

    ## Flowcharts Upload in sentinelUploads ExtBlob code start here

    def loadsentinelFlowCharts(self):
        """
        @description : This method is used to load flow chart
        @return: Loaded Flowcharts

        """
        self.tmp_dir = tempfile.mkdtemp()
        rst = self.Sentinel.SentinelModel.getAllFlowcharts()
        for each_rcd in rst:
            flowchartdoc_name = each_rcd['name']  #1
            tmp_file = os.path.join(self.tmp_dir,each_rcd['RULE_DOC'])
            tmp_file_obj = open(tmp_file, 'wb')
            tmp_file_obj.write(each_rcd['DATA'])   #4 writing data to temp file
            tmp_file_obj.close()
            self.sentinelUploads.manage_addProduct['ExtBlob'].manage_addExtBlob(id=str(flowchartdoc_name),
                                                                                title=each_rcd['RULE_TITLE'],
                                                                                descr="Created from dataload",
                                                                                file=tmp_file,
                                                                                content_type='',
                                                                                permission_check=0)

    ## Education Materials Upload in Edu_material ExtBlob code start here

    def displayFlowchartPDF(self):
        """
        @description : This method is used to display flow chart pdf.
        @return: returns pdf view for print,
                 with data elements replaced with empty lines
                 for nurses to enter data manaually
        """

        request = self.REQUEST
        rule_doc = int(request.get('rule_doc', 0))
        enclosure_idn = rule_doc.split('_')[0]
        return self.createPdfDocumentPrint(notice_idn)

    def showActions(self):
        """
        @description : This method is used to return the screen to display all actions
        @return: Returns a page which will allow you to attach action(s)
        """
        request = self.REQUEST
        I_CONTEXT_ID = request.get('I_CONTEXT_ID','')
        header_type = ''
        rule_src_id = ''
        if request.has_key('header_type'):
            header_type = request['header_type']
        if request.has_key('rule_src_id'):
            rule_src_id = request['rule_src_id']
        header = self.ZeUI.getHeader(header_type)
        footer = self.ZeUI.getFooter(header_type)
        tab_count = request.get('tabCount','')
        pop_up = request.get('pop_up','')
        dtml_document = getattr(self.views,'action_attach')
        next_page = header+dtml_document(self.views,request=request,I_CONTEXT_ID=I_CONTEXT_ID,pop_up=pop_up,tabCount=tab_count,rule_src_id=rule_src_id)+footer
        return next_page

    def changeRuleAction(self):
        """
        @description : This method is used to change rule action.
        @return : return empty.
        """
        REQUEST = self.REQUEST
        I_RULE_IDN = REQUEST['I_RULE_IDN']
        entity_active = REQUEST['I_ENTITY_ACTIVE'].strip()
        user_idn = (int(self.cms.ZeUser.Model.getLoggedinUserIdn()) or 3)
        self.Sentinel.SentinelModel.changeActionForRule(i_rule_idn= I_RULE_IDN,\
                                                        i_entity_active = entity_active,\
                                                        i_user_idn = user_idn)
        return ' '

    def changeRuleSetAction(self):
        """
        @description : This method is used to change rule set action.
        @return : return empty.
        """
        REQUEST = self.REQUEST
        pkg_id = REQUEST['I_PKG_IDN']
        entity_active = REQUEST['I_ENTITY_ACTIVE'].strip()
        user_idn = (int(self.cms.ZeUser.Model.getLoggedinUserIdn()) or 3)
        self.Sentinel.SentinelModel.changeActionForRuleSet(\
                                                           i_pkg_idn= pkg_id,\
                                                           i_entity_active = entity_active,\
                                                           i_user_idn = user_idn)
        REQUEST.set('info_alert', self.ZeUtil.getJivaMsg(msg_code = '017'))
        return ' '

    def checkActiveRules(self):
        """
        @description : This method is used to check active rule.
        @return : return 1 or empty based on rule.
        """
        REQUEST = self.REQUEST
        I_RULE_IDN = REQUEST['I_RULE_IDN']
        rs = self.Sentinel.SentinelModel.showPkgDetailsForRuleId(rule_id = I_RULE_IDN).dictionaries()
        if rs:
            return 1
        rule_label = self.Sentinel.SentinelModel.getSelectedRuleDetails(rule_id = I_RULE_IDN).dictionaries()
        if REQUEST['action'] == 'activate':
            if rule_label[0]['LABEL']:
                label_results = self.Sentinel.SentinelModel.is_label_in_use(rule_label[0]['LABEL'],rule_idn=I_RULE_IDN).dictionaries()
                if label_results:
                    return '0'
        return ' '

    def changeCriteriaStatus(self):
        """
        @description : This method is used to change rule action.
        @return : return empty.
        """
        REQUEST = self.REQUEST
        I_CRITERIA_IDN = REQUEST['I_CRITERIA_IDN']
        entity_active = REQUEST['I_ENTITY_ACTIVE'].strip()
        user_idn = (int(self.cms.ZeUser.Model.getLoggedinUserIdn()) or 3)
        self.Sentinel.SentinelModel.changeCriteriaStatus(i_criteria_idn=I_CRITERIA_IDN, 
                                                         i_entity_active = entity_active,
                                                         i_user_idn = user_idn)
        return ' '

    def changeActionStatus(self):
        """
        @description : This method is used to change rule action.
        @return : return empty.
        """
        REQUEST = self.REQUEST
        I_ACTION_IDN = REQUEST['I_ACTION_IDN']
        entity_active = REQUEST['I_ENTITY_ACTIVE'].strip()
        user_idn = (int(self.cms.ZeUser.Model.getLoggedinUserIdn()) or 3)
        self.Sentinel.SentinelModel.changeActionStatus(i_action_idn=I_ACTION_IDN, 
                                                       i_entity_active = entity_active,
                                                       i_user_idn = user_idn)
        return ' '

    def checkRulesForActions(self):
        """
        @description : This method is used to check active rule.
        @return : return 1 or empty based on rule.
        """
        REQUEST = self.REQUEST
        I_ACTION_IDN = REQUEST['I_ACTION_IDN']
        rs = self.Sentinel.SentinelModel.checkRulesForActions(action_id = I_ACTION_IDN).dictionaries()
        if rs:
            return 1
        return ' '

    def checkRulesForCriteria(self):
        """
        @description : This method is used to check active rule.
        @return : return 1 or empty based on rule.
        """
        REQUEST = self.REQUEST
        I_CRITERIA_IDN = REQUEST['I_CRITERIA_IDN']
        rs = self.Sentinel.SentinelModel.checkRulesForCriteria(criteria_id = I_CRITERIA_IDN).dictionaries()
        if rs:
            return 1
        return ' '

    def showRuleSetPreviewPage(self):
        """
        @description : This method is used to show rule set preview page.
        @return : return rule set preview page.
        """
        request = self.REQUEST
        header_type=''
        if request.has_key('header_type'):
            header_type = request['header_type']
        header = self.ZeUI.getHeader(header_type)
        footer = self.ZeUI.getFooter(header_type)
        rule_id = request.get('rule_id','0')
        I_CONTEXT_ID = request.get('I_CONTEXT_ID','')
        if rule_id <> '0':
            rule_set_details_list = self.Sentinel.SentinelModel.\
                                  selectRuleSetPreviewDetails(\
                                      rule_id=rule_id
                                      ).dictionaries()
            dtml_document = getattr(self.views, 'rule_set_preview_details')
            next_page = header+dtml_document(self.views,
                                             request=request,
                                             rule_set_details_list=rule_set_details_list,
                                             rule_id=rule_id,
                                             I_CONTEXT_ID=I_CONTEXT_ID
                                             )+footer
        return next_page

    def genereateRuleDescriptors(self):
        """
        @description : This method is used to generate rule descriptors.
        @return : return rule descriptor page.
        """
        request = self.REQUEST
        inp_param = request.get('inp_param','')
        header_type = ''
        if request.has_key('header_type'):
            header_type = request['header_type']
        header = self.ZeUI.getHeader(header_type)
        footer = self.ZeUI.getFooter(header_type)
        rule_id = inp_param.split(',')
        result_set = self.Sentinel.SentinelModel.selectRuleValuesByTitle(\
            rule_id=rule_id
            ).dictionaries()
        noResultMsg=self.ZeUtil.getJivaMsg(msg_code='470')
        act_cri_result_set = self.getRuleActionCriteriaDetails(rule_id=rule_id[0])[0]
        dtml_document = getattr(self.views, 'show_rule_descriptor_detail_page')
        return header+dtml_document(self.views, REQUEST=request,
                                    result_set = result_set,
                                    act_cri_result_set = act_cri_result_set,
                                    inp_param = inp_param
                                    )+footer

    def genereateRulessetDescriptors(self):
        """
        @description : This method is used to generate rule set descriptors.
        @return : return rule set descriptor page.
        """
        request = self.REQUEST
        inp_param = request.get('inp_param','')
        header_type = ''
        if request.has_key('header_type'):
            header_type = request['header_type']
        header = self.ZeUI.getHeader(header_type)
        footer = self.ZeUI.getFooter(header_type)
        rule_id_list = []
        act_criteria_list = []
        noResultMsg = self.ZeUtil.getJivaMsg(msg_code='470')
        if request.get('rule_src_idn')!='3':
            result_set = self.Sentinel.SentinelModel.showPackageDetailsforPkgId(pkg_id=inp_param).dictionaries()
            dtml_document = getattr(self.views, 'show_rulesset_descriptor_detail_page')
        else:
            result_set = self.getAssmntDetails(ruleset_id=inp_param)
            if len(result_set)==0:
                request.set('warning','No corresponding published assessment found. Please deactivate rule set and create new one')
            dtml_document = getattr(self.views, 'show_assmnt_rulesset_descriptor_page')
        return header+dtml_document(self.views, REQUEST=request,
                                    result_set = result_set,
                                    inp_param = inp_param
                                    )+footer
    
    def getAssmntDetails(self,ruleset_id):
        """
        """
        assmnt_ruleset_dtls={}
        assmnt_result = self.Sentinel.SentinelModel.getAssessmentDetailsForRulesetId(ruleset_id=ruleset_id).dictionaries()
        for each in assmnt_result:
            assmnt_ruleset_dtls['PKG_DESCRIPTION'] = each['PKG_DESCRIPTION']
            assmnt_ruleset_dtls['PKG_TITLE'] = each['PKG_TITLE']
            rule_dtls = self.getRuleDetailsforPkgId(pkg_id = each['PKG_ID'],entity_active = each['ENTITY_ACTIVE'])
            assmnt_ruleset_dtls['Rule']=[]
            for each_rule in rule_dtls:
                assmnt_rule_dtls={}
                assmnt_rule_dtls['Action']=[]
                assmnt_rule_dtls['ElseAction']=[]
                assmnt_rule_dtls['Data']=each_rule
                assmnt_rule_dtls['Criteria'] = self.Sentinel.SentinelModel.getCriteriasForRule(each_rule['SRE_RULE_IDN']).dictionaries()# get criteria results
                
                actions = self.Sentinel.SentinelModel.getRuleActionMasterDetails(each_rule['SRE_RULE_IDN']).dictionaries()# get action results
                for each_action in actions:
                    actionparams = self.Sentinel.SentinelModel.selectActionParams(each_action['SRE_ACTION_IDN']).dictionaries()
                    each_action.update(actionparams[0])
                    if each_action['EXEC_GROUP']==0:
                        assmnt_rule_dtls['Action'].append(each_action)
                    else:
                        assmnt_rule_dtls['ElseAction'].append(each_action)
                assmnt_ruleset_dtls['Rule'].append(assmnt_rule_dtls)
        return assmnt_ruleset_dtls

    def showKeywordPage(self):
        """
        @description : This method is used to show keyword page.
        @return : return keyword page.
        """
        request = self.REQUEST
        header_type = ''
        if request.has_key('header_type'):
            header_type = request['header_type']
        header = self.ZeUI.getHeader(header_type)
        footer = self.ZeUI.getFooter(header_type)
        I_CONTEXT_ID = request.get('I_CONTEXT_ID','')
        noResultMsg = self.ZeUtil.getJivaMsg(msg_code='510')
        dtml_document = getattr(self.views, 'keyword_list')
        return header+dtml_document(self.views, REQUEST=request,I_CONTEXT_ID =I_CONTEXT_ID,noResultMsg=noResultMsg)+footer

    ### History Code Start Here ###
    def getKeywordsHistoryPage(self):
        """
        @description : This method is used to get keyword history page.
        @return : Keywords History page
        """
        request = self.REQUEST
        dtml_page = self.views.keywords_history
        request.set('is_pop_up',request.get('is_pop_up'))
        type_id = request.get('type_id',0)
        scrtype = request.get('scrtype','')
        user_idn = self.ZeUser.Model.getLoggedinUserIdn()
        if scrtype=='package':
            search_result = self.Sentinel.SentinelModel.getPkgKeywordsHistoryResult(pkg_id=type_id)
        else:
            search_result = self.Sentinel.SentinelModel.getRuleKeywordsHistoryResult(rule_id=type_id)
        type = 'adv_pop_up'
        header = self.ZeUI.getHeader(type,'WorkLoad List')
        footer = self.ZeUI.getFooter(type)
        return header+dtml_page(self.views,REQUEST = request,search_result=search_result)+footer

    ### History Code End Here ###

    def addKeywordsForEntity(self):
        """
        @description : This method is used for show keyword search page.
        @return : return to keyword search page.
        """
        request = self.REQUEST
        dtml_page = self.views.keyword_search
        return dtml_page(self.views,
                         REQUEST = request)

    def keywordsEntitySearchResult(self):
        """
        @description : This method is used for show keyword search result page.
        @return : Keyword Search AS per Search Char/text
        """
        request = self.REQUEST
        request.set('log_event_type', 'add')
        request.set('log_event_name', 'keyword_add')
        request.set('log_main_location', 'intake')
        request.set('log_sub_location', 'case_intake')
        keyword_cd = request.get('I_KEYWORD','')
        type_id = request.get('type_id',0)
        scrtype = request.get('scrtype','')
        header_type = ''
        if request.has_key('header_type'):
            header_type = request['header_type']
        header = self.ZeUI.getHeader(header_type)
        footer = self.ZeUI.getFooter(header_type)
        if scrtype == 'package':
            search_result = self.Sentinel.SentinelModel.getKeywordsforPkgResults(keyword_cd=keyword_cd,pkg_id=type_id)
        else:
            search_result = self.Sentinel.SentinelModel.getKeywordsforRuleResults(keyword_cd=keyword_cd,rule_id=type_id)
        noResultMsg = self.ZeUtil.getJivaMsg(msg_code='563')
        dtml_page = self.views.keywords_entity_search_result
        return header+dtml_page(self.views,
                                REQUEST = request,
                                search_result=search_result,
                                noResultMsg=noResultMsg)+footer


    def getExistingKeywordsList(self):
        """
        @description : This method is used to show Existing Keywords List for that Entity
        @return : Existing Keywords List for that Entity
        """
        request = self.REQUEST
        keyword_idn = request.get('I_KEYWORD_IDN')
        type_id = request.get('type_id',0)
        scrtype = request.get('scrtype','')
        I_CONTEXT_ID = request.get('I_CONTEXT_ID','')
        request.set('log_event_type', 'add')
        request.set('log_event_name', 'keyword_add')
        if request.has_key('I_ENTITY_ACTIVE') and request['I_ENTITY_ACTIVE']=='N':
            request.set('log_event_type','update')
            request.set('log_event_name','keyword_deactivate')
        elif request.has_key('I_ENTITY_ACTIVE') and request['I_ENTITY_ACTIVE']=='Y':
            request.set('log_event_type','update')
            request.set('log_event_name','keyword_activate')

        request.set('info_alert',request.get('info_alert',''))
        noResultMsg = self.ZeUtil.getJivaMsg(msg_code='564')
        user_idn = self.ZeUser.Model.getLoggedinUserIdn()
        if scrtype=='package':
            if request.get('add'):
                self.Sentinel.SentinelModel.insertPkgKeywords(pkg_id = type_id,
                                                              keyword_idn = keyword_idn,
                                                              user_idn = user_idn)
                request.set('info_alert', self.ZeUtil.getJivaMsg(msg_code = '453'))
            search_result = self.Sentinel.SentinelModel.getRuleSetKeywords(rule_set_id=type_id)
        else:
            if request.get('add'):
                self.Sentinel.SentinelModel.insertRuleKeywords(rule_id = type_id,
                                                               keyword_idn = keyword_idn,
                                                               user_idn = user_idn)
                request.set('info_alert', self.ZeUtil.getJivaMsg(msg_code = '453'))
            search_result = self.Sentinel.SentinelModel.getRuleKeywords(rule_id=type_id)
        dtml_page = self.views.keywords_existing_list
        header = self.ZeUI.getHeader()
        footer = self.ZeUI.getFooter()
        return header+dtml_page(self.views,REQUEST = request,
                                search_result=search_result,
                                noResultMsg=noResultMsg,
                                type_id=type_id,
                                scrtype=scrtype,
                                I_CONTEXT_ID=I_CONTEXT_ID)+footer

    def getkeywordActivateDeactivate(self):
        """
        @description : This method is used to get keyword are Activate/Deactivate.
        @return : Activate/Deactivate button page
        """

        request = self.REQUEST
        entity_keyword_id = request.get('I_TYPE_KWD_IDN')
        entity_active = request.get('I_ENTITY_ACTIVE','Y')
        type_id = request.get('type_id')
        scrtype = request.get('scrtype')
        user_idn = self.ZeUser.Model.getLoggedinUserIdn()
        if scrtype=='package':
            self.Sentinel.SentinelModel.activateDeactivatePkgkeyword(entity_keyword_id,entity_active,user_idn)
        else:
            self.Sentinel.SentinelModel.activateDeactivateRulekeyword(entity_keyword_id,entity_active,user_idn)
        if  entity_active =='N':
            msg_code = '016'
        elif entity_active =='Y':
            msg_code = '017'
        request.set('info_alert', self.ZeUtil.getJivaMsg(msg_code = msg_code))
        return self.Sentinel.SentinelController.getExistingKeywordsList()

    def getMappedRule(self):
        """
        @description : This method is used get mapped rule.
        @return :rule title.
        """
        request = self.REQUEST
        formname = request.get('form', '')
        table_id = request.get('table_id','')
        if formname == 'reference_table':
            rule_result = self.Sentinel.SentinelModel.getActiveRulesMappedToRefTable(ref_table_id = int(table_id),rule_flag='Y').dictionaries()
        elif formname == 'decision_table':
            rule_result = self.Sentinel.SentinelModel.getActiveRulesMappedToDecTable(dec_table_id = int(table_id),rule_flag='Y',criteria_flag='N',action_flag='N').dictionaries()
        else:
            rule_result = ''
        rule_title = ''
        count = 1
        if rule_result:
            for dict_id in rule_result:
                rule_title+='\n'+str(count)+'.'+dict_id['RULE_TITLE']
                count+=1
            return'%s,%s,%s'%('1',rule_title,'rules')
        else:
            if formname == 'reference_table':
                result_set = self.Sentinel.SentinelModel.getActiveRulesMappedToRefTable(ref_table_id = int(table_id),rule_flag='N').dictionaries()
                criteria_title = ''
                count = 1
                if result_set:
                    for dict_id in result_set:
                        criteria_title+='\n'+str(count)+'.'+dict_id['CRITERIA_TITLE']
                        count+=1
                    return'%s,%s,%s'%('1',criteria_title,'criteria')
                else:
                    return'%s,%s'%('0','')
            elif formname == 'decision_table':
                criteria_set = self.Sentinel.SentinelModel.getActiveRulesMappedToDecTable(dec_table_id = int(table_id),rule_flag='N',criteria_flag='Y',action_flag='N').dictionaries()
                action_set = self.Sentinel.SentinelModel.getActiveRulesMappedToDecTable(dec_table_id = int(table_id),rule_flag='N',criteria_flag='N',action_flag='Y').dictionaries()
                criteria_title = ''
                action_title = ''
                if criteria_set:
                    count = 1
                    for dict_id in criteria_set:
                        criteria_title+='\n'+str(count)+'.'+dict_id['CRITERIA_TITLE']
                        count+=1
                if action_set:
                    count = 1
                    for dict_id in action_set:
                        action_title+='\n'+str(count)+'.'+dict_id['ACTION_TITLE']
                        count+=1
                if criteria_set and action_set:
                    criteria_action = "\n"+"List of Criteria:"+criteria_title
                    criteria_action+= "\n\n"+"List of Action:"+action_title
                    return'%s,%s,%s'%('1',criteria_action,'criteria and action')
                elif criteria_set:
                    return'%s,%s,%s'%('1',criteria_title,'criteria')
                elif action_set:
                    return'%s,%s,%s'%('1',action_title,'action')
                else:
                    return'%s,%s'%('0','')

    def deActivateReferenceTable(self):
        """
        @description : This method is used for deactive the reference table
        @return : de activates reference table if it is not mapped in any active rule.
        """
        request = self.REQUEST
        try:
            user_idn = int(self.cms.ZeUser.Model.getLoggedinUserIdn())
        except:
            user_idn = 3
        ref_table_id = request.get('ref_table_id','')
        self.Sentinel.SentinelModel.deActivateRefValue(ref_table_id = ref_table_id, user_idn=user_idn)
        self.Sentinel.SentinelModel.deActivateRefColumn(ref_table_id = ref_table_id, user_idn=user_idn)
        self.Sentinel.SentinelModel.deActivateRefTable(ref_table_id = ref_table_id, user_idn=user_idn)
        request.set('info_alert', self.ZeUtil.getJivaMsg(msg_code = '713'))
        sel_value = self.addRefTable(ref_table_id='')
        return sel_value

    def deActivateDecisionTable(self):
        """
        @description : This method is used for deactive the decision table
        @return : de activates decision table if it is not mapped in any active rule.
        """
        request = self.REQUEST
        try:
            user_idn = int(self.cms.ZeUser.Model.getLoggedinUserIdn())
        except:
            user_idn = 3
        dec_table_id = request.get('dec_table_id','')
        self.Sentinel.SentinelModel.deActivateDecTable(dec_table_id = dec_table_id, user_idn=user_idn)
        request.set('info_alert', self.ZeUtil.getJivaMsg(msg_code = 'V50204101'))
        sel_value = self.addDecisionTable(dec_table_id='')
        return sel_value   

    def getActInnerParamsPage(self,sub_sel_name=None,inner_params={}):
        """
        @description : This method is used to get second level action parameters
        page for the selected action script
        @return : This function return page based on action script.
        """
        request = self.REQUEST
        I_CONTEXT_ID = request.get('I_CONTEXT_ID','')
        new_action_script = request.get('episode_type', None)
        sel_dec_table = request.get('sel_dec_table', None)
        check_dec_table = request.get('check_dec_table','')
        action_id = request.get('action_id',0)
        sel_div_index = request.get('I_SEL_DIV_INDEX','')
        action_id = request.get('action_id',0)
        dec_table_idn = ''
        param_name = request.get('param_name','')
        param_list = {}
        param_set = self.Sentinel.SentinelModel.selectActionParams(\
            action_idn = action_id).dictionaries()
        if param_set:
            for param in param_set:
                if param['PARAM_NAME'] and param['PARAM_VALUE']:
                    param_list[param['PARAM_NAME']] =\
                              param['PARAM_VALUE']
            if param_list.has_key('I_SEL_DIV_INDEX') and \
               param_list['I_SEL_DIV_INDEX']:
                sel_div_index = param_list['I_SEL_DIV_INDEX']
                dec_table_idn = param_list['dec_table_idn'+sel_div_index]
                dec_table_colno = param_list['dec_table_column_num'+sel_div_index]
                param_name = param_list['I_PARAM_NAME'+sel_div_index]
        views = self.Sentinel.SentinelController.views.views_act_types
        if (sub_sel_name or new_action_script) or sel_dec_table:
            if check_dec_table:
                script_name = 'act_param_decision_table'
                dtml_document = getattr(views, script_name)
            else:
                script_name = 'act_param_' + (sub_sel_name or new_action_script)
                dtml_document = getattr(views, script_name)
            return dtml_document(views, 
                                 act_param_details = inner_params, 
                                 I_CONTEXT_ID = I_CONTEXT_ID, 
                                 I_SEL_DIV_INDEX=sel_div_index,
                                 I_DEC_TABLE_IDN_WITH_INDEX=dec_table_idn,
                                 I_PARAM_NAME=param_name,
                                 REQUEST=request)
        else:
            return views.act_param_none()

    def getActSecondlevelParamsPage(self,sub_sel_name=None,inner_params={}):
        """
        @description : This method is used to get second level action parameters page for the selected action script
        @return : This function return page based on selected action script.
        """
        #needs tp make changes to this method and use a common method to all level of params
        request = self.REQUEST
        new_action_script = request.get('second_level', None)
        I_CONTEXT_ID = request.get('I_CONTEXT_ID','')
        views = self.Sentinel.SentinelController.views.views_act_types
        dec_table_idn = request.get('I_DEC_TBL_IDN','')
        sel_div_index = request.get('I_SEL_DIV_INDEX','')
        decision_column_names = request.get('dec_col_names'+sel_div_index,'')
        action_id = request.get('action_id',0)
        param_list = {}
        param_set = self.Sentinel.SentinelModel.selectActionParams(\
            action_idn = action_id).dictionaries()

        if param_set:
            for param in param_set:
                if param['PARAM_NAME'] and param['PARAM_VALUE']:
                    param_list[param['PARAM_NAME']] =\
                              param['PARAM_VALUE']
            if param_list.has_key('I_SEL_DIV_INDEX') and param_list['I_SEL_DIV_INDEX']:
                sel_div_index = param_list['I_SEL_DIV_INDEX']
                dec_table_idn = param_list['dec_table_idn'+sel_div_index]
                dec_table_colno = param_list['dec_table_column_num'+sel_div_index]
        if decision_column_names:
            script_name = 'act_param_' + decision_column_names
            dtml_document = getattr(views, script_name)
            return dtml_document(views, 
                                 act_param_details = inner_params, 
                                 REQUEST=request, 
                                 I_CONTEXT_ID = I_CONTEXT_ID,
                                 I_DEC_TABLE_IDN_WITH_INDEX=dec_table_idn,
                                 I_SEL_DIV_INDEX=sel_div_index)

        if (sub_sel_name or new_action_script):
            if isinstance(new_action_script,list) and len(new_action_script)>1:
                script_name = 'act_param_' + (sub_sel_name or new_action_script[0])
            else:
                script_name = 'act_param_' + (sub_sel_name or new_action_script)
            dtml_document = getattr(views, script_name)
            return dtml_document(views, 
                                 act_param_details = inner_params, 
                                 REQUEST=request, 
                                 I_CONTEXT_ID = I_CONTEXT_ID,
                                 I_DEC_TABLE_IDN_WITH_INDEX=dec_table_idn,
                                 I_SEL_DIV_INDEX=sel_div_index)
        else:
            return views.act_param_none()

    def getDecisionTableColumnNames(self, sel_div_index=None):
        """
        @description : This method is used to pull decision table column names
        @return : This function return page based on selected action script.
        """
        request = self.REQUEST
        dec_table_idn = ''
        if sel_div_index:
            dec_table_idn = request.get('dec_table_idn'+sel_div_index,'')
        action_id = request.get('action_id',0)

        param_list = {}
        param_set = self.Sentinel.SentinelModel.selectActionParams(\
            action_idn = action_id).dictionaries()
        if param_set:
            for param in param_set:
                if param['PARAM_NAME'] and param['PARAM_VALUE']:
                    param_list[param['PARAM_NAME']] =\
                              param['PARAM_VALUE']
            if param_list.has_key('I_SEL_DIV_INDEX') and param_list['I_SEL_DIV_INDEX']:
                I_SEL_DIV_INDEX = param_list['I_SEL_DIV_INDEX']
                dec_table_idn = param_list['dec_table_idn'+sel_div_index]
                dec_table_colno = param_list['dec_table_column_num'+sel_div_index]
        #page_info = self.getPageDetails()
        #col_data=self.Sentinel.SentinelModel.selectDecisionTableDetail(\
                                            #dec_table_idn=dec_table_idn,
                                            #query_from=page_info['I_START_REC_NO'],
                                            #query_to=page_info['I_END_REC_NO']
                                            #).dictionaries()
        #col_data.reverse()
        #headers = col_data.pop()
        #dic = {}
        #for each in headers:
            #dic[each.split('col')[1]]=headers[each].strip()
        #return dic
        headers = {}
        db_type = self.ZeUtil.isOracle()
        if db_type:
            col_data = self.getDecisionTableInfo(dec_table_idn=dec_table_idn,row_id='/table/row[1]',db_type=db_type,row_start=1,row_end=1,order_by='DESC').tuples()[0]
        else:
            col_data = self.getDecisionTableInfo(dec_table_idn=dec_table_idn,row_id='/row[1]').tuples()[0]
        for i in range(len(col_data)):
            headers[str(int(i))] = col_data[i]
        return headers

    def getSelectedRuleDetails(self, rule_id=None):
        """
        @description : This method is used to get selected rule
        @return : This function returns Rule Id with Rule Title.
        """
        request = self.REQUEST
        rule_id = str(rule_id)
        if not rule_id:
            rule_id = request.get('rule_id','')
        rule_id = rule_id.split(',')
        for i in (range(rule_id.__len__())):
            if rule_id[i] == '':
                del rule_id[i]
        id_title = {}
        ruleid_tile = ''
        rule_id_str = ','.join(rule_id)
        rule_detail = self.Sentinel.SentinelModel.getSelectedRuleDetails(rule_id=rule_id_str).dictionaries()
        for i in range(0,rule_detail.__len__()):
            idn = rule_detail[i]['ID']
            title = rule_detail[i]['TITLE']
            source_idn = rule_detail[i]['SRC_IDN']
            source_cd = rule_detail[i]['SRC_CD']
            title = quote(title) # (quote) is used to define Uniform Resource Identifier
            id_title[str(idn)] = title+'@@'+str(source_idn)+'@@'+str(source_cd)
        for j in range(0,rule_id.__len__()):
            ruleid_tile+=rule_id[j]+'@@'+id_title[rule_id[j]]+'$$$'
        return ruleid_tile

    def showUpdateReferenceTablePage(self):
        """
        @description : This method is used to show update reference table page.
        @return: return to update reference table page.
        """
        request = self.REQUEST
        ref_table_id = request.get('ref_table_id',0)
        ref_table_name = request.get('ref_table_name','')
        header_type = ''
        if request.has_key('header_type'):
            header_type = request['header_type']
        header = self.ZeUI.getHeader(header_type)
        footer = self.ZeUI.getFooter(header_type)
        dtml_page = getattr(self.views,'update_reference_table')
        return header+dtml_page(self.views,
                                REQUEST = request,
                                ref_table_name=ref_table_name,
                                ref_table_id=ref_table_id
                                )+footer

    def showAppendReferenceTablePage(self):
        """
        @description : This method is used to show append reference table page.
        @return: return to append reference table
        """
        request = self.REQUEST
        ref_table_id = request.get('ref_table_id',0)
        ref_table_name = request.get('ref_table_name','')
        header_type = ''
        if request.has_key('header_type'):
            header_type = request['header_type']
        header = self.ZeUI.getHeader(header_type)
        footer = self.ZeUI.getFooter(header_type)
        dtml_page = getattr(self.views,'append_reference_table')
        return header+dtml_page(self.views,
                                REQUEST = request,
                                ref_table_name=ref_table_name,
                                ref_table_id=ref_table_id
                                )+footer

    def replaceURIComponent(self,myStr, quote_flag='Y'):
        """
        @description : This method is used to replace string to Uniform Resource Identifier
        @param : myStr {string} any string
        @param : quote_flag {string} either quote or unquote decided based on this flag
        @return: return with Uniform Resource Identifier
        """
        if myStr:
            if quote_flag == 'Y':
                myStr = quote(myStr)
            else:
                myStr = unquote(myStr)
        return myStr

    def showSimulationEventPage(self):
        """
        @description : This method is used to show simulation event page
        @return: return to show simulation event page
        """
        request = self.REQUEST
        dtml_page = getattr(self.views,'show_simulation_event')
        return dtml_page(self.views,REQUEST = request,I_CONTEXT_ID='')

    def getSimulationResultPage(self):
        """
        @description : This method is used to get simulation result page.
        @return : return to simulation result page
        """
        request = self.REQUEST
        event_idn = request.get('event_idn','').split('@')[0]
        noResultMsg=self.ZeUtil.getJivaMsg(msg_code='627')
        # pagination
        page_info = self.getPageDetails()

        tot_sim_count = self.Sentinel.\
                      SentinelModel.\
                      selectRuleDetailsCount(\
                          event_id=event_idn,
                          enabled='Y'
                          )[0][0]

        sim_recordset = self.Sentinel.\
                      SentinelModel.\
                      selectRuleDetails(\
                          event_id=event_idn,
                          enabled='Y',
                          query_from=page_info['I_START_REC_NO'],
                          query_to=page_info['I_END_REC_NO']
                      )
        sim_list = sim_recordset.dictionaries()
        action_title = ''
        criteria_title = ''
        count = 0;
        for loop in sim_list:
            criteria = self.Sentinel.SentinelModel.get_criteria_details_for_rule(loop['ID']).dictionaries()
            action = self.Sentinel.SentinelModel.get_action_details_for_rule(loop['ID']).dictionaries()
            criteria_count = 0
            action_count = 0
            block = 0
            for iloop in range(0,criteria.__len__()):
                for jloop in range(0,criteria.__len__()):
                    if criteria_count == criteria[jloop]['EXEC_GROUP']:
                        if block == criteria_count:
                            criteria_title+='Block'+str(int(criteria_count)+1)+': '+'<br>'
                            block = criteria_count + 1
                        criteria_title+=criteria[jloop]['CRITERIA_TITLE']+'<br>'
                criteria_count = criteria_count + 1
                block = criteria_count
            block = 0
            for iloop in range(0,action.__len__()):
                for jloop in range(0,action.__len__()):
                    if action_count == action[jloop]['EXEC_GROUP']:
                        if block == action_count:
                            action_title+='Block'+str(int(action_count)+1)+': '+'<br>'
                            block = action_count + 1
                        action_title+=action[jloop]['TITLE']+'<br>'
                action_count = action_count + 1
                block = action_count
            sim_list[count]['BLOCK_CRITERIA'] = criteria_title
            sim_list[count]['BLOCK_ACTION'] = action_title
            action_title = ''
            criteria_title = ''
            count = count + 1
        dtml_document = getattr(self.views, 'simulation_result_page')
        return dtml_document(self.views, REQUEST=request,
                             sim_list=sim_list,
                             evnet_idn = event_idn,
                             total_rec=tot_sim_count,

                             I_CUR_PG=page_info['I_CUR_PAGE'],
                             noResultMsg=noResultMsg
                             )

    def getEpisodeInnerParamsPage(self,sub_sel_name=None,inner_params=None):
        """
        @description : This method is used to get episode inner action parameter page.

        @param : sub_sel_name {string} script name.
        @param : inner_params {string} parameter dictionary.
        @return : This function return page based on action script name
        """
        request = self.REQUEST
        I_CONTEXT_ID = request.get('I_CONTEXT_ID','')
        new_action_script = request.get('episode_type', None)
        if new_action_script == None:
            new_action_script=sub_sel_name
        views = self.Sentinel.SentinelController.views.views_act_types
        if new_action_script in ('CM','QR','BH-CM'):
            new_action_script='CM'
        elif new_action_script in ('DM','Coach', 'MM', 'HP', 'BH'):
            new_action_script='DM'
        elif new_action_script in ('LCN','RECON', 'TRANSPLANT', 'ReConsideration'):
            new_action_script='LCN'
        elif new_action_script in ('IP','OP','OP Referral','PR','PD','BH-OP','BH-IP'):
            new_action_script='IP'
        elif new_action_script in ('Appeal','2nd Appeal', 'ALJ', 'DSHS', 'Appeal-Recon', 'IRO', 'COC'):
            new_action_script='APPEAL'
        elif new_action_script in ('INQ'):
            new_action_script='INQUIRY'
        elif new_action_script in ('MemSvc'):
            new_action_script='CALL'
        else:
            new_action_script=None
        common_slot = getattr(views, 'encounter_view_common_slot')
        common_slot = common_slot(views, act_param_details = inner_params, I_CONTEXT_ID = I_CONTEXT_ID, REQUEST=request)
        if new_action_script:
            script_name = 'act_param_encounter_view_' + (new_action_script).lower()
            episode_specific_details = getattr(views, script_name)
            episode_specific_details = episode_specific_details(views, act_param_details = inner_params, I_CONTEXT_ID = I_CONTEXT_ID, REQUEST=request)
            dtml_page = common_slot+episode_specific_details
        else:
            dtml_page = common_slot
        
        return dtml_page

    def getAutoAssignmentStatus(self):
        """
        @description : Method to get Auto Assignment Status
        @return : return Auto Assignment Status
        """
        return constants.AUTO_ASSIGNMENT_EPISODE_STATUS

    def get_episode_status(self,episode_type=None):
        """
        @description : Method to get Episode Status
        @return : return episode status based on episode type
        """
        status_list=[]
        if episode_type:
            available_status = self.WorkFlow.Controller.getEpisodeStatusForAssignTo(episode_type,initial_status_only=False)
            status_set=set([status_data['status'] for status_data in available_status])
            status_list=list(status_set)
            if episode_type in ('CM','DM'):
                status_list.append(constants.AUTO_ASSIGNMENT_EPISODE_STATUS)
        return status_list
    
    def showRuleAttributePage(self):
        """
        Returns the Attach Attributes page where we can attach
        attributes to a keyword or remove the attributes attached
        to a keyword.
        @return: Attaching Attributes page
        """
        request = self.REQUEST
        rule_idn = int(request.get('rule_idn',0))
        rule_title = request.get('rule_attr_title','')
        header = self.ZeUI.getHeader()
        footer = self.ZeUI.getFooter()
        dtml_page = self.views.attach_rule_attributes
        return header + dtml_page(self.views,
                                  REQUEST=request,
                                  rule_title=rule_title,
                                  rule_idn=rule_idn) + footer

    def attachRuleAttributes(self):
        """
        Attaches the selected Attribute Values and the corresponding
        Attributes for a particular rule.
          - If the Attribute value is already attached to the rule
            and was in Inactive state, it will activate the
            corresponding value.
          - If the Attribute value is removed from the attached list,
            it will deactivate the corresponding value.
          - If attribute value was not attached and added to the
            selected list, it will attach(inserts) to the question.
        @return: show attach page
        """
        request = self.REQUEST
        rule_idn = int(request.get('rule_idn',0))
        user_idn = int(self.ZeUser.Model.getLoggedinUserIdn())
        attribute_value_idns = request.get('attribute_value_idn',[])
        deact_update_idns = request.get('deactive_attr_idn','')
        if deact_update_idns.endswith(','):
            deact_update_idns = deact_update_idns[:-1]

        # Update Deactive Rule Attributes
        if deact_update_idns:
            self.Sentinel.SentinelModel.updateRuleAttributes(\
                rule_idn=rule_idn,
                attribute_value_idn=deact_update_idns,
                entity_active='N',
                user_idn=user_idn)
        # Update Active Rule Attributes
        if attribute_value_idns:
            attribute_value_idns = ','.join(attribute_value_idns)
            self.Sentinel.SentinelModel.updateRuleAttributes(\
                rule_idn=rule_idn,
                attribute_value_idn=attribute_value_idns,
                entity_active='Y',
                user_idn=user_idn)
        # Insert Rule Attributes
            self.Sentinel.SentinelModel.insertRuleAttributes(\
                rule_idn=rule_idn,
                attribute_value_idn=attribute_value_idns,
                user_idn=user_idn)
        if attribute_value_idns:
            request.set('info_alert',self.ZeUtil.getJivaMsg(msg_code='765'))
        else:
            request.set('info_alert','')
        return self.showRuleAttributePage()

    def getSreAttributeValues(self):
        """
        Returns the available list of Attribute Values for a particular
        Attribute selected, by getting the attribute idn from the
        REQUEST
        @return: List of question attribute values page
        """
        request = self.REQUEST
        attribute_idn = request.get('attribute_idn',0)
        I_CONTEXT_ID = request.get('context_id','')
        sFrmName = request.get('sFrmName','')
        dtml_page = self.views.sre_attribute_values
        record_set = self.Assessment.Model.zsqls.getAttributeValues(
            question_attribute_idn=attribute_idn,
            entity_active='Y')
        return dtml_page(self.views,
                         REQUEST=request,
                         I_CONTEXT_ID=I_CONTEXT_ID,
                         sFrmName=sFrmName,
                         record_set=record_set)

    def showRuleSetAttributePage(self):
        """
        Returns the Attach Attributes page where we can attach
        attributes to a keyword or remove the attributes attached
        to a keyword.
        @return: Attaching Attributes page
        """
        request = self.REQUEST
        pkg_id = int(request.get('pkg_id',0))
        rule_set_title = request.get('rule_set_title','')
        header = self.ZeUI.getHeader()
        footer = self.ZeUI.getFooter()
        dtml_page = self.views.attach_rule_set_attributes
        return header + dtml_page(self.views,
                                  REQUEST=request,
                                  rule_set_title=rule_set_title,
                                  pkg_id=pkg_id) + footer

    def attachRuleSetAttributes(self):
        """
        Attaches the selected Attribute Values and the corresponding
        Attributes for a particular rule.
          - If the Attribute value is already attached to the rule
            and was in Inactive state, it will activate the corresponding value.
          - If the Attribute value is removed from the attached list,
            it will deactivate the corresponding value.
          - If attribute value was not attached and added to the
            selected list, it will attach(inserts) to the question.
        @return: show attach page
        """
        request = self.REQUEST
        pkg_id = int(request.get('pkg_id',0))
        user_idn = int(self.ZeUser.Model.getLoggedinUserIdn())
        attribute_value_idns = request.get('attribute_value_idn',[])
        deact_update_idns = request.get('deactive_attr_idn','')
        if deact_update_idns.endswith(','):
            deact_update_idns = deact_update_idns[:-1]

        # Update Deactive Rule Set Attributes
        if deact_update_idns:
            self.Sentinel.SentinelModel.updateRuleSetAttributes(\
                pkg_id=pkg_id,
                attribute_value_idn=deact_update_idns,
                entity_active='N',
                user_idn=user_idn)
        # Update Active Rule Set Attributes
        if attribute_value_idns:
            attribute_value_idns = ','.join(attribute_value_idns)
            self.Sentinel.SentinelModel.updateRuleSetAttributes(\
                pkg_id=pkg_id,
                attribute_value_idn=attribute_value_idns,
                entity_active='Y',
                user_idn=user_idn)
            # Insert Rule Attributes
            self.Sentinel.SentinelModel.insertRuleSetAttributes(\
                pkg_id=pkg_id,
                attribute_value_idn=attribute_value_idns,
                user_idn=user_idn)
        if attribute_value_idns:
            request.set('info_alert',self.ZeUtil.getJivaMsg(msg_code='767'))
        else:
            request.set('info_alert','')
        return self.showRuleSetAttributePage()

    def getSvcCtgyPage(self,sub_sel_name=None,inner_params={}):
        """
        @description : This method is used to get second level action parameters page for the selected action script
        @return : This function return page based on action script.
        """
        request = self.REQUEST
        I_CONTEXT_ID = request.get('I_CONTEXT_ID','')
        new_action_script = 'svc_ctgy'
        views = self.Sentinel.SentinelController.views.views_act_types
        if (sub_sel_name or new_action_script):
            script_name = 'act_param_' + (sub_sel_name or new_action_script)
            dtml_document = getattr(views, script_name)
            return dtml_document(views, act_param_details = inner_params, I_CONTEXT_ID = I_CONTEXT_ID, REQUEST=request)
        else:
            return views.act_param_none()

    def showRuleCriteriaPreviewPage(self):
        """
        @description : This method is used to show rule preview page.
        @return : return rule preview page.
        """
        request = self.REQUEST
        criteria_id = request.get('criteria_id','0')
        I_CONTEXT_ID = request.get('I_CONTEXT_ID','')
        noResultMsg = self.ZeUtil.getJivaMsg(msg_code='769')
        header_type = ''
        if request.has_key('header_type'):
            header_type = request['header_type']
        header = self.ZeUI.getHeader(header_type)
        footer = self.ZeUI.getFooter(header_type)
        if criteria_id <> '0':
            rule_details_list = self.Sentinel.SentinelModel.\
                              selectRuleCriteriaPreviewDetails(\
                                  criteria_id=criteria_id
                                  ).dictionaries()
            dtml_document = getattr(self.views, 'rule_criteria_preview_details')
            next_page = header+dtml_document(self.views,
                                             request=request,
                                             rule_details_list=rule_details_list,
                                             criteria_id=criteria_id,
                                             I_CONTEXT_ID=I_CONTEXT_ID,
                                             noResultMsg=noResultMsg
                                             )+footer
        return next_page

    def showRuleActionPreviewPage(self):
        """
        @description : This method is used to show rule preview page.
        @return : return rule preview page.
        """
        request = self.REQUEST
        action_id = request.get('action_id','0')
        I_CONTEXT_ID = request.get('I_CONTEXT_ID','')
        noResultMsg = self.ZeUtil.getJivaMsg(msg_code='768')
        header_type = ''
        if request.has_key('header_type'):
            header_type = request['header_type']
        header = self.ZeUI.getHeader(header_type)
        footer = self.ZeUI.getFooter(header_type)
        if action_id <> '0':
            rule_details_list = self.Sentinel.SentinelModel.\
                              selectRuleActionPreviewDetails(\
                                  action_id=action_id
                                  ).dictionaries()
            dtml_document = getattr(self.views, 'rule_action_preview_details')
            next_page = header+dtml_document(self.views,
                                             request=request,
                                             rule_details_list=rule_details_list,
                                             action_id=action_id,
                                             I_CONTEXT_ID=I_CONTEXT_ID,
                                             noResultMsg=noResultMsg
                                             )+footer
        return next_page
    ####JIVA5 UI Refactoring related code Ends here#####
    ####Export and Import of Actions related code Starts here#####

    security.declareProtected('Ze Sentinel ViewExportAction', 'showExportActionSearchPage')
    def showExportActionSearchPage(self):
        """
        @description : This method is used to show export rule search page.
        @return : return to export rule search page.
        """
        request = self.REQUEST
        dtml_document = getattr(self.views, 'export_action_search')
        next_page = dtml_document(self.views, REQUEST=request)
        return next_page

    def showActionExportToXlPage(self):
        """
        This method returns DTML page with content type set as application ms excel.
        DTML page contains all data related to actions selected for export.
        """
        request = self.REQUEST

        action_ids = request.get('cid','')
        action_type = request.get('action_script', '')
        action_title = request.get('action_title', '')
        action_filter = request.get('filter_enabled', '')
        if action_ids:
            action_ids = action_ids.split(',')

        action_search_parameters = {'act_type':action_type, 'act_title':action_title, 'act_filter':action_filter}

        actions_record_set = self.Sentinel.SentinelModel.get_action_details(action_ids, action_search_parameters)

        actions_list = self.get_action_details_for_export(actions_record_set=actions_record_set)
        # If no action records found, raise error
        if not actions_list:
            raise Exception("No action details found")

        excel_object_url = action_export(self, actions_list)

        return request.RESPONSE.redirect(excel_object_url)
        
        # The below commented section to be deleted when
        # export export functionality has been approved
        #=======================================================================
        # dtml_document = getattr(self.views, 'export_action')
        # return header+dtml_document(self.views,
        #                            REQUEST=request,
        #                            actions_list=actions_list)+footer
        #=======================================================================

    def get_action_details_for_export(self, actions_record_set):
        """
        @ param : actions_record_set - result set object - result set containing action details

        Return details for given action and action parameters (in form of list of dictionaries)
        Each dictionary corresponds to action record.
        """
        action_export_map_dict = constants.ACTION_PARAM_EXPORT_MAP
        actions_list = actions_record_set.dictionaries()
        for each_action in actions_list:
            each_action['PARAM_NAME'] = ''
            each_action['PARAM_VALUE'] = ''

            each_action_id = each_action['SRE_ACTION_IDN']
            # Get action parameters details using action parameter table
            action_parameters_record_set = self.Sentinel.SentinelModel.selectActionParams(action_idn=each_action_id)
            action_parameters_list = action_parameters_record_set.dictionaries()

            if action_parameters_list:
                parameter_name_string = ''
                parameter_value_string = ''
                # Loop over each action parameter and create string for parameter value and name
                for param_index,param_dict in enumerate(action_parameters_list):
                    parameter_name = param_dict['PARAM_NAME']
                    parameter_value = param_dict['PARAM_VALUE']
                    # If action parameter value available and refers to code table data, we need to get corresponding
                    # description/title etc using existing id given in parameter value
                    if (parameter_name in action_export_map_dict) and parameter_value:
                        parameter_export_tuple = action_export_map_dict[parameter_name]
                        parameter_select_table = parameter_export_tuple[0]
                        parameter_where_clause = parameter_export_tuple[1]
                        parameter_select_column = parameter_export_tuple[2]

                        parameter_query = "%s = '%s'" % (parameter_where_clause, str(parameter_value))
                        parameter_result_set = self.Sentinel.SentinelModel.getTableData(tbl_name=parameter_select_table,
                                                                                        sel_col=parameter_select_column,
                                                                                        sql_query=parameter_query)
                        if parameter_result_set:
                            # There should only one record in code table for given id
                            parameter_result = parameter_result_set.dictionaries()[0]

                            # Overwrite existing parameter value with new id
                            parameter_value=parameter_result[parameter_select_column]

                    # Initialize parameter name/value string only once i.e for first action parameter
                    if param_index == 0:
                        parameter_name_string = parameter_name
                        parameter_value_string = parameter_value
                    else:
                        # If not first action parameter - append name and value to existing parameter name, value string
                        parameter_name_string += '~~' + parameter_name
                        parameter_value_string += '~~' + parameter_value

                # Update action record set to include parameter name and value details
                # - in string format separated by ~~
                each_action['PARAM_NAME'] = parameter_name_string
                each_action['PARAM_VALUE'] = parameter_value_string

        return actions_list

    ####Export and Import of Actions related code Ends here#####

    def getConsolidatedSearchResults(self,col_name, value, prefix='', suffix=''):
        """
        @ col_name : Column Name
        @ value : value
        @ prefix : defines whether we need to put % before word
        @ suffix : defines whether we need to put % after word
        Returns Like expession
        The different set of options how like is currently used in jiva
        ##%value%  --- value
        ##value%   --- ^value
        ##%value   --- value$
        ##value    --- ^value$
        """
        ret_val = ''
        if value:
            re_val = re.search(re_exp,value)
            if (re_val == None):
                rep_val = re.search("[']",value)
                if rep_val:
                    value = value.replace("'","''")
            else:
                value = value.replace("'","")

            val_lst = value.split(',')
            str_lst = []
            for each in val_lst:
                str_lst.append(" %s LIKE %s%s%s " % (col_name, zesql_binding_placeholder_begin, prefix + each + suffix, zesql_binding_placeholder_end))
            ret_val = '('+'or'.join(str_lst)+')'
        return ret_val

    #def getCustomCriteriaFields(self):
        #""" 
        #@description : This method is used to get custom criteria fields for the selected entity attribute              
        #"""
        #request = self.REQUEST
        #entity_attr_idn = int(request.get('entity_attribute', ''))
        #I_CONTEXT_ID = request.get('I_CONTEXT_ID','')
        #ident_custom_pattern = EntityAttr.load(self, idn=entity_attr_idn).populate_additional_values()
        #customFieldLength = len(ident_custom_pattern)
        #label={}
        #custom_fields = {}
        #for i in range(len(ident_custom_pattern)):
            #label[ident_custom_pattern[i].split(':')[0][3:-1]] = ident_custom_pattern[i].split(':')[2][1:-3]
            #custom_fields[ident_custom_pattern[i].split(':')[0][3:-1]] = ident_custom_pattern[i].split(':')[1]
            #dtml_document = getattr(self.views, 'custom_criteria_page')
            #return dtml_document(self.views,
                                    #I_CONTEXT_ID = I_CONTEXT_ID,
                                    #REQUEST=request,
                                    #custom_fields=custom_fields,
                                    #customFieldLength=customFieldLength,
                                    #label=label)

    ######## Decision Table Code Starts here ##########
    def getDecisionTableFields(self):
        """
        Get Criteria fields for Decision Table Criteria
        """
        request = self.REQUEST
        I_CONTEXT_ID = request.get('I_CONTEXT_ID', '')
        dec_tble_operators = constants.DECISION_TABLE_OPERATORS_DICT
        dtml_document = getattr(self.views, 'decision_table_criteria_page')
        return dtml_document(self.views,
                             REQUEST = request,
                             operators=dec_tble_operators,
                             I_CONTEXT_ID = I_CONTEXT_ID)

    def getDecisionTableNames(self, dec_table_id=''):
        """
        Get Decision Table Names
        """
        request = self.REQUEST
        if not dec_table_id:
            dec_table_id = request.get('dec_table_id','')
        decision_table_details = self.Sentinel.SentinelModel.getDecisionTableDetails(dec_table_id=dec_table_id).dictionaries()
        return decision_table_details

    def getDecTableColumns(self, dec_table_id,template_call = 'N'):

        """
        Get Decision Table Column Names
        """
        request = self.REQUEST
        dec_table_id = request.get('dec_table_id', '')
        col_details = {}
        if dec_table_id:
            #decision_column_details = self.getDecisionTableInfo(dec_table_idn=dec_table_id,row_id='')
            db_type = self.ZeUtil.isOracle()
            if db_type:
                col_names = self.getDecisionTableInfo(dec_table_idn=dec_table_id,row_id='/table/row[1]',db_type=db_type,row_start=1,row_end=1,order_by='DESC').tuples()[0]
            else:
                col_names = self.getDecisionTableInfo(dec_table_idn=dec_table_id,row_id='/row[1]').tuples()[0]
            if template_call == 'N':
                result_set='<select align="left" name="dec_column_num" class="mandatorychk">\
                                    <option value="">---Select One---</option>'
                for i in range(len(col_names)):
                    col_details[i] = col_names[i]
                    result_set+="<option value="+str(i)+">"+col_names[i]+"</option>"
                result_set+='</select>'
                return result_set
            else:
                for i in range(len(col_names)):
                    col_details[str(i)] = col_names[i]
                return col_details
        else:
            if template_call == 'N':
                result_set='<select align="left" name="dec_column_num" class="mandatorychk">\
                                    <option value="">---Select One---</option> </select>'
                return result_set
            else:
                return col_details

    #def getDecTableColumns(self, dec_table_id,template_call = 'N'):

        #"""
        #Get Decision Table Column Names
        #"""
        #request = self.REQUEST
        #dec_table_id = request.get('dec_table_id', '')
        #decision_column_details = self.Sentinel.SentinelModel.getDecisionTableColumnDetails(dec_table_id=dec_table_id).dictionaries()
        #decision_column_details.reverse()
        #headers = decision_column_details.pop()
        #col_num = headers.keys()
        #col_name = headers.values()
        #col_details = {}
        #if template_call == 'N':
            #result_set='<select align="left" name="dec_column_numR1" class="mandatorychk">\
                                #<option value="">---Select One---</option>'
            #for i in range(0, len(headers)):
                    #dec_col = re.compile('col(\d+)')
                    #col_no = dec_col.search(col_num[i]).group(1)
                    #col_details[col_no] = col_name[i]
                    #result_set+="<option value="+col_no+">"+headers['col'+col_no] +"</option>"
            #result_set+='</select>'
            #return result_set
        #else:
            #for i in range(0, len(headers)):
                    #dec_col = re.compile('col(\d+)')
                    #col_no = dec_col.search(col_num[i]).group(1)
                    #col_details[col_no] = col_name[i]
            #return col_details

    def showDecisionTableRuleAddPage(self):
        """
        @description : This method is used to show Decision Table Rule Add Page
        """
        request = self.REQUEST
        output_entity = constants.OUTPUT_ENTITY
        I_CONTEXT_ID = request.get('I_CONTEXT_ID','')
        dtml_document = getattr(self.views, 'dec_rules_add_page')
        header = self.ZeUI.getHeader('Add Decision Table Rule')
        footer = self.ZeUI.getFooter()
        next_page = header+dtml_document(self.views,
                                         request=request,
                                         I_CONTEXT_ID = I_CONTEXT_ID,
                                         output_entity = output_entity)+footer
        return next_page
    ######## Decision Table Code Ends here ##########

    def getRuleSourceTypes(self,src_description = ''):
        """
        Displays all the Rule Source Types
        """
        request    = self.REQUEST
        if not src_description:
            src_description     = request.get('src_description','')
        return self.Sentinel.SentinelModel.getRuleSourceTypes(src_description=src_description).dictionaries()

    ####JIVA5 UI Refactoring related code Ends here#####
    security.declareProtected('Ze Sentinel ViewImportAction', 'showImportActionPage')
    def showImportActionPage(self):
        """
        @description : This method is used to show import rule set page.
        @return : return to show import rule set page
        """
        request = self.REQUEST
        header_type = ''
        if request.has_key('header_type'):
            header_type = request['header_type']
        header = self.ZeUI.getHeader(header_type)
        footer = self.ZeUI.getFooter(header_type)
        dtml_document = getattr(self.views, 'import_action_page')
        return header+dtml_document(self.views, REQUEST=request)+footer

    ####Export and Import of Actions related code Ends here#####
    def getCustomCriteriaFields(self):
        """ 
        @description : This method is used to get custom criteria fields for the selected entity attribute              
        """
        request = self.REQUEST
        header_type = ''
        if request.has_key('header_type'):
            header_type = request['header_type']
        header = self.ZeUI.getHeader(header_type)
        footer = self.ZeUI.getFooter(header_type)
        dtml_document = getattr(self.views, 'custom_criteria_page')
        I_CONTEXT_ID = request.get('I_CONTEXT_ID','')
        entity_attr_idn = request.get('entity_attribute', '')
        if entity_attr_idn:
            ident_custom_pattern = EntityAttr.load(self, idn=int(entity_attr_idn)).populate_additional_values()
            customFieldLength = len(ident_custom_pattern)
            label={}
            custom_fields = {}
            for i in range(len(ident_custom_pattern)):
                label[ident_custom_pattern[i].split(':')[0][3:-1]] = ident_custom_pattern[i].split(':')[2][1:-3]
                custom_fields[ident_custom_pattern[i].split(':')[0][3:-1]] = ident_custom_pattern[i].split(':')[1]
            return header+dtml_document(self.views,
                                        I_CONTEXT_ID = I_CONTEXT_ID,
                                        REQUEST=request,
                                        custom_fields=custom_fields,
                                        customFieldLength=customFieldLength,
                                        label=label)+footer
        else:
            return header+dtml_document(self.views,
                                        I_CONTEXT_ID = I_CONTEXT_ID,
                                        REQUEST=request,
                                        custom_fields='',
                                        customFieldLength='',
                                        label='')+footer

    security.declareProtected('Ze Sentinel ConfigureAssessmentEntities', 'showAssessmentEntities')
    def showAssessmentEntities(self):
        """
        Loads Assessment Entities
        """
        request = self.REQUEST
        assessment_type = self.Assessment.Model.getAssessmentTypes().dictionaries()
        dtml_document = getattr(self.views, 'assessment_entities_page')
        header_type = ''
        if request.has_key('header_type'):
            header_type = request['header_type']
        header = self.ZeUI.getHeader(header_type)
        footer = self.ZeUI.getFooter(header_type)
        next_page = header+dtml_document(self.views,
                                         request = request,
                                         assessment_type = assessment_type)+footer
        return next_page

    def load_assessment_entities(self, assmt_type=None, assmt_ctgy_cd=None, assmt_status='Published'):
        """
        @ param : enc_type - string - encounter type
        @ param : assmt_ctgy_cd - string - assessment category
        @ param : assmt_status - string - assessment status

        Loads assessment rules related entities for given assessment template
        (based on encounter type assessment category and status)

        Add records to code_sre_entity table for each master question of given assessment template.
        """
        log_message = ''
        request = self.REQUEST

        if not assmt_ctgy_cd:
            assmnt_name_split =  request.get('assmnt_name').split('~~')
            assmnt_title_id = assmnt_name_split[0]
            assmnt_title = assmnt_name_split[1]

        if not assmt_type:
            assmt_type_split = request.get('assmnt_type').split('~~')
            assmt_type_id = assmt_type_split[0]
            assmt_type = assmt_type_split[1]
        rule_type = request.get('rule_type')
        criteria_type = request.get('criteria_type')
        if assmnt_title and assmt_status and assmt_type:
            try:
                logged_in_user = int(self.cms.ZeUser.Model.getLoggedinUserIdn())
            except:
                logged_in_user = 3

            assessment_template_recordset = self.Assessment.Model.getAssessments(assmnt_status=assmt_status,
                                                                                 assmnt_title=assmnt_title_id,
                                                                                 assmnt_type=assmt_type_id)

            if not assessment_template_recordset:
                return "Not able to load entities, as there are no assessment template with %s status" % assmt_status

            if len(assessment_template_recordset) > 1:
                return "Not able to load entities, as there are more than one assessment template with %s status" % assmt_status

            assessment_template_id = assessment_template_recordset[0]['ACE_TEMPLATE_IDN']

            assessment_questions_recordset = self.Sentinel.SentinelModel.getAssessmentQuestionDetails(template_id=assessment_template_id)

            entity_name = 'Assessment'
            table_name = 'master_qstn'
            column_name = 'master_qstn_idn'

            for eachQuestion in assessment_questions_recordset:
                question_id = eachQuestion.MASTER_QSTN_IDN
                question_text = eachQuestion.QSTN_TXT
                ext_qstn_cd = eachQuestion.EXT_QSTN_CD

                entity_objects = EntityAttr.load_many(context=self,
                                                      name=entity_name,
                                                      attr=ext_qstn_cd,
                                                      tbl_names=table_name,
                                                      assessment_template=assessment_template_id,
                                                      question=question_id,
                                                      is_active='Y')
                if not entity_objects:
                    try:
                        entity = EntityAttr.insert(context=self,
                                                   desc=question_text,
                                                   name=entity_name,
                                                   attr=ext_qstn_cd,
                                                   title=question_text,
                                                   rule_type=rule_type,
                                                   criteria_type=criteria_type,
                                                   tbl_names=table_name,
                                                   col_names=column_name,
                                                   user_idn=logged_in_user,
                                                   assessment_template=assessment_template_id,
                                                   question=question_id)
                        entity.save()
                        log_message += "\n Successfully created new entity defination with name %s and attribute %s " % (entity_name,question_text)
                    except Exception,e:
                        log_message += '\n ---------------Error log----------------\n'
                        log_message += '\n ERROR - %s %s \n' % (str(datetime.today().strftime("%a, %d %b %Y %H:%M:%S")),str(e))

                else:
                    log_message += "\n Entity with details - name:%s, attribute:%s already exists" % (entity_name, question_text)

            log_message += "\n Successfully loaded assessment rules related entity definitions into the database."
        else:
            log_message += "\n Required information about assessment template is not provided"

        if request:
            log_message = re.sub("\n","<br/>",log_message)
        return log_message

    def getPublishedAceTitles(self):
        """
        Gets the list of categories
        Related Tables : master_ace_title
        @param enc_type_cd : Episode Type
        @return : List of Assessment summary
        Returns Category Types Available
        """
        request = self.REQUEST
        i_assmnt_type = int(request.get('assmnt_type','').split('~~')[0])
        catlist = []
        sel_attr='<select name="assmnt_name" class="mandatorychk">\
                               <option value="">---Select One---</option>'

        recs = self.Assessment.Model.getAssessments(assmnt_title='',\
                                                    assmnt_type=i_assmnt_type,\
                                                    assmnt_status='Published',\
                                                    assmnt_temp_idn='',\
                                                    mod_type='ace',\
                                                    from_rec='',\
                                                    to_rec='')
        for r in recs:
            sel_attr+='<option value="'+str(r.ACE_TITLE_IDN)+'~~'+str(r.ACE_TITLE_DESCRIPTION)+'">'+\
                    str(r.ACE_TITLE_DESCRIPTION)+'</option>'
        sel_attr+='</select>'

        return sel_attr    

    def modifyUploadDecisionTable(self):
        """
        @description : This method to modify/upload Decision table.
        Script to modify / upload Decision table
        Read excel sheet
        @return : return to Decision result page.
        """
        request = self.REQUEST
        user_idn = int(self.cms.ZeUser.Model.getLoggedinUserIdn())
        uploaded_file = request.get('upload_dec', '')
        filename=r"%s" % str(uploaded_file.filename)
        dec_file_name = filename.split('\\')[-1]
        cwd = os.path.abspath(os.path.dirname(__file__))
        base_path = os.path.join(cwd,'decision_table')
        if not os.path.exists(base_path):
            os.mkdir(base_path)
        dec_file_path = os.path.join(base_path, dec_file_name)
        raw_file = uploaded_file.read()
        f = file(dec_file_path, 'wb')
        f.write(raw_file)                   # write text to file
        f.close()
        if not os.path.isfile(dec_file_path):
            raise NameError, "%s is not a valid filename" % dec_file_path
        
        # Modify Decision Table Related Changes Started Here
        dec_table_id = request.get('deact_dec_tab_idn','')
        tblname = {True:request.get('dec_table_title', ''), False:request.get('upd_dec_tab_name', '')}[dec_table_id == '']
        db_type = self.ZeUtil.isOracle()
        if db_type: # ORACLE
            if dec_table_id:
                mod_result = self.insertUpdateDecisionTable(dec_table_id=dec_table_id,dec_file_path=dec_file_path,tblname=tblname,db_type=db_type)
                request.set('info_alert', self.ZeUtil.getJivaMsg(msg_code = 'V50204104'))
                if mod_result.split('@@')[0] == 'N':
                    return'%s@@%s'%('N','') # This Rerurn indicate Modifiy Transaction are Failed
                else:
                    sel_value = self.addDecisionTable(dec_table_id=dec_table_id)
                    return'%s@@%s@@%s@@%s'%('Y',sel_value,tblname,dec_table_id) # This Rerurn indicate Successfully Modified
            else:
                insert_result = self.insertUpdateDecisionTable(dec_table_id=dec_table_id,dec_file_path=dec_file_path,tblname=tblname,db_type=db_type)
                request.set('info_alert', self.ZeUtil.getJivaMsg(msg_code = 'V50204102'))
                if insert_result.split('@@')[0] == 'Y':
                    dec_table_id = insert_result.split('@@')[1]
                    request.set('dec_tbl_id', dec_table_id)
                    sel_value = self.addDecisionTable(dec_table_id=dec_table_id)
                    return'%s@@%s@@%s@@%s'%('Y',sel_value,tblname,dec_table_id) # This Rerurn indicate Successfully Inserted
                else:
                    return'%s@@%s'%('N','') # This Rerurn indicate insert Transaction are Failed
        else: # MSSQL
            if dec_table_id:
                mod_result = self.updateDecisionTable(dec_table_id=dec_table_id,dec_file_path=dec_file_path,tblname=tblname)
                request.set('info_alert', self.ZeUtil.getJivaMsg(msg_code = 'V50204104'))
                if mod_result.split('@@')[0] == 'N':
                    return'%s@@%s'%('N','') # This Rerurn indicate Modifiy Transaction are Failed
                else:
                    sel_value = self.addDecisionTable(dec_table_id=dec_table_id)
                    return'%s@@%s@@%s@@%s'%('Y',sel_value,tblname,dec_table_id) # This Rerurn indicate Successfully Modified
            else:
                request.set('info_alert', self.ZeUtil.getJivaMsg(msg_code = 'V50204102'))
            # Modify Decision Table Related Changes Ended Here
        
        spreadsheet = Spreadsheet(dec_file_path)
        xml_expr = spreadsheet.as_XML(sheetid=0, max_rows='12')
        if isinstance(xml_expr,tuple):
            return'%s@@%s'%(xml_expr[0],xml_expr[1]) # Column is empty or non_string validation
        if isinstance(xml_expr,str) and xml_expr !='':
            dt = Decisiontable.insert(self,
                                      name=tblname,
                                      col_data=xml_expr,
                                      user_idn=user_idn)
            request.set('dec_tbl_id', dt.idn)
            sel_value = self.addDecisionTable(dec_table_id=dt.idn)
            return'%s@@%s@@%s@@%s'%('Y',sel_value,tblname,dt.idn)
        
    def insertUpdateDecisionTable(self,dec_table_id='',dec_file_path='',tblname='',db_type=''):
        """
        @description : This method is used to Insert decision table.
        @return: return to Inserted decision table page.
        """
        request = self.REQUEST
        i_user_idn = int(self.cms.ZeUser.Model.getLoggedinUserIdn())
        if dec_file_path:
            wb = xlrd.open_workbook(dec_file_path)
            sheets = wb.sheet_names()
            empty_result = self.emptyCheck(sheets=sheets,eobj=wb) # Validate Excel Sheet are Empty or Header have any (Empty Header)
            if db_type: # ORACLE Related Changes
                if not empty_result:
                    return'%s@@%s'%('N','') # Either any one Header are Empty
                if dec_table_id:
                    header_name = self.getDecisionTableInfo(dec_table_idn=dec_table_id,row_id='/table/row[1]',db_type=db_type,row_start=1,row_end=1,order_by='DESC').tuples()[0]
                    header_result = self.ValidateHeaders(e_header=header_name,sheets=sheets,eobj=wb)
                    if not header_result:
                        return'%s@@%s'%('N','') # Either any one Header are Empty
                for name in sheets:
                    sh = wb.sheet_by_name(name)
                    headerRow = sh.row_values(0)
                    col_data = '<table><row>'
                    for col in range(len(headerRow)):
                        col_data += '<col'+str(col)+'>'+self.ZeUtil.encode(headerRow[col])+'</col'+str(col)+'>'
                    col_data += '</row></table>'
                    if not dec_table_id:
                        tbl_idn = self.Sentinel.SentinelModel.insertDecisionTbl(tblname=tblname,col_data=col_data,user_idn=i_user_idn,db_type=db_type)[0]['SRE_DECISION_TBL_IDN']
                    else:
                        self.Sentinel.SentinelModel.emptyDecTableData(\
                             i_dec_table_id=dec_table_id,
                             i_empty_stmt=col_data, 
                             i_user_idn=i_user_idn
                            )
                        tbl_idn = dec_table_id
                    for traverse_row in range(1,sh.nrows):
                        types,values = sh.row_types(traverse_row),sh.row_values(traverse_row)
                        else_flag = ''
                        # Add One Row at the End of XML
                        i_temp_stmt,i_updt_stmt = '<row>','<row>'
                        for col in range(len(headerRow)):
                            col_value = self.formatrow(types[col], values[col], 0)
                            try:
                                col_value = str(col_value)
                            except UnicodeError:
                                chars = []
                                for char in values[col]:
                                    try:
                                        chars.append(char.encode('ascii', 'strict'))
                                    except UnicodeError:
                                        chars.append('&#%i;' % ord(char))
                                col_value = ''.join(chars)
                            i_updt_stmt += '<col'+str(col)+'>temp_data'+'</col'+str(col)+'>'
                            if str(col_value).find("'") >= 0 or str(col_value).find("''") >= 0 or str(col_value).find('"') >= 0 or str(col_value).find('&') >= 0:
                                else_flag = 'Y' # Using this flag we are differentiate whether only append or (append and update) row.
                            col_value = str(col_value).replace("<","&lt;").replace(">","&gt;")
                            i_temp_stmt += '<col'+str(col)+'>'+self.ZeUtil.encode(col_value)+'</col'+str(col)+'>'
                        i_temp_stmt += '</row>'
                        i_updt_stmt += '</row>'
                        if len(i_temp_stmt) < 4000 and not else_flag:
                            self.Sentinel.SentinelModel.addNewDecisionTableRow(i_dec_table_id=tbl_idn,i_updt_stmt=repr(i_temp_stmt),i_user_idn=i_user_idn)
                        else:
                            self.Sentinel.SentinelModel.addNewDecisionTableRow(i_dec_table_id=tbl_idn,i_updt_stmt=repr(i_updt_stmt),i_user_idn=i_user_idn)
                            for indx in range(len(headerRow)):
                                cell_value = self.formatrow(types[indx], values[indx], 0)
                                try:
                                    cell_value = str(cell_value)
                                except UnicodeError:
                                    chars = []
                                    for char in values[indx]:
                                        try:
                                            chars.append(char.encode('ascii', 'strict'))
                                        except UnicodeError:
                                            chars.append('&#%i;' % ord(char))
                                    cell_value = ''.join(chars)
                                if len(cell_value) <= 3986: # Column length should be less than 3986 character
                                    if str(cell_value).find('&') >= 0:
                                        cell_value = str(cell_value).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace("'","''")
                                        add_node = '<col'+str(indx)+'>'+cell_value+'</col'+str(indx)+'>'
                                        insert_stmt = repr('/table/row['+str(int(traverse_row+1))+']')+', '+repr('col'+str(indx))+', XMLType('"'"+add_node+"'"')'
                                        del_stmt = repr('/table/row['+str(int(traverse_row+1))+']/col'+str(indx)+'[1]')
                                        try:
                                            self.Sentinel.SentinelModel.updateDecisioneRow(insert_stmt=insert_stmt,del_stmt=del_stmt,dec_table_id=tbl_idn,user_idn=i_user_idn)
                                        except:
                                            return'%s@@%s'%('N','')
                                    else:
                                        cell_value = str(cell_value).replace("<","&lt;").replace(">","&gt;").replace("'","''")
                                        xml_path = repr('/table/row['+str(int(traverse_row+1))+']/col'+str(indx)+'[1]/text()')
                                        i_updt_stmt = "'"+self.ZeUtil.encode(cell_value)+"'"
                                        try:
                                            self.Sentinel.SentinelModel.updateDecisioneRow(dec_table_id=tbl_idn,i_updt_stmt=i_updt_stmt,xml_path=xml_path,user_idn=i_user_idn)
                                        except:
                                            return'%s@@%s'%('N','')
                                else:
                                    return'%s@@%s'%('N','')
                    if dec_table_id:
                        Decisiontable.load(self, idn=tbl_idn).refresh_all_columnar_criteria()
                        Decisiontable.load(self, idn=tbl_idn).refresh_all_columnar_actions()
                    break
                return'%s@@%s'%('Y',tbl_idn) # Successfully Inserted
        
    def updateDecisionTable(self,dec_table_id='',dec_file_path='',tblname='',db_type=''):
        """
        @description : This method is used to update decision table.
        @return: return to updateed decision table page.
        """
        request = self.REQUEST
        try:
            i_user_idn = int(self.cms.ZeUser.Model.getLoggedinUserIdn())
        except:
            i_user_idn = 3
        if dec_table_id and dec_file_path:
            wb = xlrd.open_workbook(dec_file_path)
            sheets = wb.sheet_names()
            empty_result = self.emptyCheck(sheets=sheets,eobj=wb) # Validate Excel Sheet are Empty or Header have any (Empty Header)
            if empty_result:
                row_id = '/row['+str(1)+']'
                tot_rec = self.getDecisionTableInfo(dec_table_idn=dec_table_id,row_id=row_id)
                header_name = tot_rec.tuples()[0]
                header_result = self.ValidateHeaders(e_header=header_name,sheets=sheets,eobj=wb)
                if header_result:
                    #This Block is used to Delete Existing Node
                    self.Sentinel.SentinelModel.emptyDecTableData(\
                        i_dec_table_id=dec_table_id,
                        i_empty_stmt='', 
                        i_user_idn=i_user_idn
                    )
                    for name in sheets:
                        sh = wb.sheet_by_name(name)
                        headerRow = sh.row_values(0)
                        for traverse_row in range(sh.nrows):
                            types,values = sh.row_types(traverse_row),sh.row_values(traverse_row)
                            header_indx = 0
                            i_updt_stmt = 'insert <row> '
                            for i in range(len(values)):
                                i_updt_stmt += '<col'+str(i)+'>temp_data'+'</col'+str(i)+'>'
                            i_updt_stmt = {True:i_updt_stmt +'</row> as first into (/)[1]', False:i_updt_stmt +'</row> as last into (/)[1]'}[traverse_row == 0]
                            self.Sentinel.SentinelModel.addNewDecisionTableRow(i_dec_table_id=dec_table_id,i_updt_stmt=repr(i_updt_stmt),i_user_idn=i_user_idn)
                            for indx in range(0,len(values)):
                                if header_indx<len(headerRow):
                                    cell_value = self.formatrow(types[indx], values[indx], 0)
                                    try:
                                        cell_value = str(cell_value)
                                    except UnicodeError:
                                        chars = []
                                        for char in values[indx]:
                                            try:
                                                chars.append(char.encode('ascii', 'strict'))
                                            except UnicodeError:
                                                chars.append('&#%i;' % ord(char))
                                        cell_value = ''.join(chars)
                                    cell_value = str(cell_value).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace("'","''")
                                    add_node = '<col'+str(indx)+'>'+cell_value+'</col'+str(indx)+'>'
                                    insert_stmt = "'"+'insert' +add_node+ ' as last into (row['+str(traverse_row+1)+'])'+"'"
                                    del_stmt = repr('delete (/row/col'+str(int(indx))+')['+str(traverse_row+1)+']')
                                    header_indx+=1
                                    insert_stmt = self.ZeUtil.encode(insert_stmt)
                                    try:
                                        self.Sentinel.SentinelModel.updateDecisioneRow(\
                                            insert_stmt=insert_stmt,
                                            del_stmt=del_stmt,
                                            dec_table_id=dec_table_id,
                                            user_idn=i_user_idn
                                            )
                                    except:
                                        return'%s@@%s'%('N','')                            
                        break
                    Decisiontable.load(self, idn=dec_table_id).refresh_all_columnar_criteria()
                    Decisiontable.load(self, idn=dec_table_id).refresh_all_columnar_actions()
                    return'%s@@%s'%('Y','') # This Rerurn indicate Successfully Modified
                else:
                    return'%s@@%s'%('N','') # This Return indicate Headers are Mismatch
            else:
                return'%s@@%s'%('N','') # This Return indicate Either any one Header are Empty
                
    def emptyCheck(self,sheets='',eobj=''):
        """
        @description : This method is used to Validate Excel Sheet are Empty or Header have any (Empty Header)
        @return: Either True/False
        """
        if sheets:
            for name in sheets:
                sh = eobj.sheet_by_name(name)
                if sh.nrows == 0:
                    return False
                else:
                    if 1 <= sh.nrows:
                        headerRow = sh.row_values(0)
                        for i in (range(headerRow.__len__())):
                            if headerRow[i] == '':
                                return False
                break
            return True
        else:
            return False
    
    def ValidateHeaders(self,e_header='',sheets='',eobj=''):
        """
        @description : This method is used to Validate Current Header is equal to Existing Headers
        @return: Either True/False
        """
        if e_header and sheets:
            match_count = 0
            for name in sheets:
                sh = eobj.sheet_by_name(name)
                c_header = sh.row_values(0)
                if c_header.__len__() != e_header.__len__():
                    return False
                for i in (range(c_header.__len__())):
                    ex_header = e_header[i].strip().replace('\n',' ')
                    ex_header = re.sub('[\s\t]+', ' ', ex_header)
                    cur_header = self.ZeUtil.encode(c_header[i].strip().replace('\n',' '))
                    cur_header = re.sub('[\s\t]+', ' ', cur_header)
                    if c_header[i] != '' and ex_header == cur_header:
                        match_count = match_count + 1
                    else:
                        if c_header[i] == '':
                            del c_header[i]
                if c_header.__len__() != e_header.__len__():
                    return False
                if match_count == e_header.__len__():
                    return True
                break
        else:
            return False

    def showUpdateDecisionTablePage(self):
        """
        @description : This method is used to show update decision table page.
        @return: return to update decision table page.
        """
        request = self.REQUEST
        dec_table_id = request.get('dec_table_id',0)
        dec_table_name = request.get('dec_table_name','')
        header_type = ''
        if request.has_key('header_type'):
            header_type = request['header_type']
        header = self.ZeUI.getHeader(header_type)
        footer = self.ZeUI.getFooter(header_type)
        dtml_page = getattr(self.views,'update_decision_table')
        return header+dtml_page(self.views,
                                REQUEST = request,
                                dec_table_name=dec_table_name,
                                dec_table_id=dec_table_id
                                )+footer

    def showMergeLabelsPage(self):
        """
        @description : This method is used to show Merge ID Pools Page
        @return 
        """
        request = self.REQUEST
        header_type=request.get('header_type','')
        header = self.ZeUI.getHeader(header_type,'')
        footer = self.ZeUI.getFooter(header_type,'')
        pkg_id = request.get('pkg_id', '')
        cur_context_id = request.get('cur_context_id','')
        I_CONTEXT_ID = request.get('I_CONTEXT_ID')
        rule_src = self.getRuleSetSource(rule_src_cd='idpool').dictionaries() # if rule_src_idn is 4 then General Rule
        rule_src_idn = rule_src[0]['SRC_IDN']
        rule_idns = [request.get('rule_idn', '')]
        rule_idns = rule_idns[0].split(',')                 
        dtml_document = getattr(self.views, 'merge_idpool_add')
        return header+dtml_document(self.views,
                                    REQUEST = request,
                                    pkg_id = pkg_id,
                                    rule_src_id = rule_src_idn,
                                    cur_context_id=cur_context_id,
                                    I_CONTEXT_ID = I_CONTEXT_ID)+footer


    def saveMergeIdPools(self):
        """
        Saves the Merge Label Details
        """
        request = self.REQUEST
        rule_title = request.get('rule_title', '')
        rule_description = request.get('rule_description', '')
        rule_execution_type = request.get('rule_execution_type','')
        rule_type = request.get('rule_type', '')
        label_left = request.get('label_left', '')
        label_right = request.get('label_right', '')
        operator = request.get('operator', '')
        event_cd = request.get('event_type', '')
        business_process = request.get('category', '')
        action_total_count = request.get('action_total_count',0)
        rule_src_idn = request.get('sre_rule_src',6) 
        user_idn=self.ZeUser.Model.getLoggedinUserIdn()
        ext_rule_cd = 'RULE'+get_base_external_cd(self)
        rule_output_label = request.get('label','')
        # Server Side validation for output label to maintain unique output label for each rule
        if not self.validate_output_label():
            return self.ZeUI.getInfoAlertSlot()
        rule_id = self.Sentinel.SentinelModel.insertRuleDetails(title=rule_title,
                                                                business_process=business_process,
                                                                rule_execution_type=rule_execution_type,
                                                                rule_type=rule_type,
                                                                rule_output_label=rule_output_label,
                                                                rule_description=rule_description,
                                                                user_id=user_idn,
                                                                event_cd=int(event_cd),
                                                                rule_src_idn=rule_src_idn,
                                                                ext_rule_cd=ext_rule_cd)[0]['SRE_RULE_IDN']
        self.Sentinel.SentinelModel.saveMergeLabels(sre_rule_idn = rule_id,
                                                    label_left=label_left,
                                                    label_right=label_right,
                                                    operator=operator,
                                                    user_idn=user_idn)
        group_count = 0
        for i in range(int(action_total_count)):
            if request.get('action_id'+str(i)):
                exec_group = request.get('action_exec_group'+str(i),'')
                action_id = request.get('action_id'+str(i),'')
                if isinstance(exec_group,str):
                    self.Sentinel.SentinelModel.insertRuleAction(rule_id=rule_id,
                                                             action_id=int(action_id.strip()),
                                                             user_id=user_idn,
                                                             priority=0,
                                                             exec_group=group_count
                                                             )
                    group_count = group_count + 1
                    
                if isinstance(exec_group,list):
                    for val in xrange(len(exec_group)):
                        self.Sentinel.SentinelModel.insertRuleAction(rule_id=rule_id,
                                                             action_id=int(action_id[val].strip()),
                                                             user_id=user_idn,
                                                             priority=val,
                                                             exec_group=group_count
                                                             )
                    group_count = group_count + 1
        return self.getSelectedRuleDetails(rule_id)
    
    def updateMergeIdPools(self):
        """
        Update the Merge Label Details
        """
        request = self.REQUEST
        rule_title = request.get('rule_title', '')
        rule_id = request.get('current_rule_idn',0)
        rule_description = request.get('rule_description', '')
        label_left = request.get('label_left', '')
        label_right = request.get('label_right', '')
        operator = request.get('operator', '')
        event_cd = request.get('event_type', '')
        business_process = request.get('category', '')
        rule_type = request.get('rule_type', '')
        rule_execution_type = request.get('rule_execution_type','')
        action_total_count = request.get('action_total_count',0)
        rule_src_idn = int(request.get('sre_rule_src',6))
        user_idn=self.ZeUser.Model.getLoggedinUserIdn()
        rule_output_label = request.get('label','')
        if not self.validate_output_label(rule_idn=rule_id):
            return self.ZeUI.getInfoAlertSlot()

        self.Sentinel.SentinelModel.updateRuleDetails(id=rule_id,
                                                      title=rule_title,
                                                      rule_category=business_process,
                                                      rule_type=rule_type,
                                                      rule_execution_type=rule_execution_type,
                                                      event_cd=event_cd,
                                                      description=rule_description,
                                                      rule_keyword='',
                                                      user_id=user_idn,
                                                      rule_doc='',
                                                      rule_src_idn=rule_src_idn,
                                                      rule_output_label=rule_output_label)


        self.Sentinel.SentinelModel.deActivateAllActionsForRule(rule_id=rule_id)
        
        self.Sentinel.SentinelModel.updateMergeLabels(rule_idn=int(rule_id),
                                                    label_left=label_left,
                                                    label_right=label_right,
                                                    operator=operator,
                                                    user_idn=user_idn)
        group_count = 0
        for i in range(int(action_total_count)):
            if request.get('action_id'+str(i)):
                exec_group = request.get('action_exec_group'+str(i),'')
                action_id = request.get('action_id'+str(i),'')
                if isinstance(exec_group,str):
                    self.Sentinel.SentinelModel.insertRuleAction(rule_id=rule_id,
                                                             action_id=int(action_id.strip()),
                                                             user_id=user_idn,
                                                             priority=0,
                                                             exec_group=group_count
                                                             )
                    group_count = group_count + 1
                    
                if isinstance(exec_group,list):
                    for val in xrange(len(exec_group)):
                        self.Sentinel.SentinelModel.insertRuleAction(rule_id=rule_id,
                                                             action_id=int(action_id[val].strip()),
                                                             user_id=user_idn,
                                                             priority=val,
                                                             exec_group=group_count
                                                             )
                    group_count = group_count + 1
        
        return self.showMergeRuleUpdatePage(update_flag='Y')
    
    def showMergeRuleUpdatePage(self,update_flag=''):
        """
        @description : This method is used to show merged rule edit page.
        @return : return to show merged rule edit page.
        """
        request = self.REQUEST
        if update_flag == 'Y':
            request.set('info_alert', self.ZeUtil.getJivaMsg(msg_code = '437'))
        header_type=request.get('header_type','')
        header = self.ZeUI.getHeader(header_type,'')
        footer = self.ZeUI.getFooter(header_type,'')
        rule_id = request.get('current_rule_idn','')
        I_CONTEXT_ID = request.get('I_CONTEXT_ID','')
        entity_active = request.get('entity_active','')
        rule_src_idn = request.get('sre_rule_src', '')
        rule_src_cd = request.get('rule_src_cd', '')
        action_set = []
        action_count = 0
        action_set = self.getRuleActionCriteriaDetails(rule_id=rule_id)[0]
        if action_set:
            action_count = len(action_set[0])
        existing_rule_idn = request.get('existing_rule_idn', '')
        rule_idns = [existing_rule_idn]
        rule_idns = rule_idns[0].split(',')
        result_set = self.Sentinel.SentinelModel.selectMergeLabels(i_rule_id = rule_id).dictionaries()
        dtml_document = getattr(self.views, 'merge_idpool_edit')
        next_page = header+dtml_document(self.views,
                                         request=request,
                                         current_rule_idn=rule_id,
                                         existing_rule_idn = existing_rule_idn,
                                         result_set=result_set,
                                         action_set=action_set,
                                         action_total_count = action_count,
                                         I_CONTEXT_ID=I_CONTEXT_ID,
                                         entity_active=entity_active,
                                         rule_src_cd=rule_src_cd,
                                         rule_src_id=int(rule_src_idn))+footer
        return next_page
    
    def viewMergeIdpoolRule(self):
        """
        @description : This method is used to view MergeIdpool Rule.
        @return : return to view mergeIdpool rule.
        """
        request = self.REQUEST
        header_type=request.get('header_type','')
        header = self.ZeUI.getHeader(header_type,'')
        footer = self.ZeUI.getFooter(header_type,'')
        rule_id = request.get('current_rule_idn','')
        I_CONTEXT_ID = request.get('I_CONTEXT_ID','')
        entity_active = request.get('entity_active','')
        action_set = []
        action_count = 0
        action_set = self.getRuleActionCriteriaDetails(rule_id=rule_id)[0]
        if action_set:
            action_count = len(action_set[0])
        result_set = self.Sentinel.SentinelModel.selectMergeLabels(i_rule_id = rule_id).dictionaries()
        dtml_document = getattr(self.views, 'merge_idpool_view')
        next_page = header+dtml_document(self.views,
                                         request=request,
                                         result_set=result_set,
                                         action_set=action_set,
                                         action_total_count = action_count,
                                         I_CONTEXT_ID=I_CONTEXT_ID,
                                         entity_active=entity_active
                                         )+footer
        return next_page
    
    def getIdpoolOperator(self):
        """
        @description : Method to get IDpool Operator
        @return : return list of operator.
        """
        return constants.IDPOOL_OPERATORS
    
    def getMergeIdpoolMappedLabel(self):
        """
        @description : Method to get IDpool Label
        @return : return Yes/No.
        """
        request = self.REQUEST
        cur_ruleid = request.get('cur_ruleid',0)
        existing_rule_idn = request.get('ruleidn', '')
        rule_idns = [existing_rule_idn]
        rule_idns = rule_idns[0].split(',')
        labels = []
        label_set = self.Sentinel.SentinelModel.selectLabelValues()
        if label_set:
            for label in label_set:
                labels.append(label['LABEL'])
        result_set = self.Sentinel.SentinelModel.selectMergeLabels(i_rule_id = cur_ruleid).dictionaries()
        label_left = result_set[0]['LABEL_LEFT']
        label_right = result_set[0]['LABEL_RIGHT']
        if label_left in labels and label_right in labels:
            return 'Y'
        else:
            return 'N'

    #Assessment Rule Set Code Started Here

    def showAddAssessmentRuleSetPage(self):
        """
        @description : This method is used to show add rule set page.
        @return : return to rule set add page.
        """
        request = self.REQUEST
        dtml_document = getattr(self.views, 'assessment_rule_set_add')
        header_type = ''
        if request.has_key('header_type'):
            header_type = request['header_type']
        header = self.ZeUI.getHeader(header_type)
        footer = self.ZeUI.getFooter(header_type)
        next_page = header+dtml_document(self.views, REQUEST=request)+footer
        return next_page

    def getRuleSetSource(self, rule_src_idn='', rule_src_cd=''):
        """
        @description : This method is used to get rule set source.
        @return : return rule source data.
        """
        ruleset_source = self.Sentinel.SentinelModel.getRuleSetSource(rule_src_idn=rule_src_idn,rule_src_cd=rule_src_cd)
        return ruleset_source

    def getQuestionTitle(self, assessment_template_idn=0):
        """
        @description : Method to get criteria title
        @param : criteria_id {int} criteria id
        @return : criteria title
        """
        request = self.REQUEST
        if assessment_template_idn == 0:
            i_assmnt_temp_idn = int(request.get('assessment_template_idn',assessment_template_idn))
        else:
            i_assmnt_temp_idn = int(assessment_template_idn)
        question_title = self.Sentinel.SentinelModel.getAssessmentQuestion(i_assmnt_temp_idn=i_assmnt_temp_idn)
        if question_title:
            questiontitle = []
            for question in question_title:
                questiontitle.append(question['QUESTION_TEXT']+'$$'+str(question['QUESTION_IDN'])+'$$'+str(question['SRE_ENTITY_IDN'])+'$$'+str(question['ENTITY_NAME']))
            return '@@'.join(questiontitle)
        else:
            return '0'

    def getRuleSetAssessementTitle(self,template='Y',i_assmnt_type=''):
        """
        @description : Method to get Assessement Title
        @param : i_assmnt_type {int} assmnt_type
        @param : i_enc_type_cd {string} episode type
        @return : Assessement Title
        """
        request = self.REQUEST
        if template == 'Y':
            i_assmnt_type = int(request.get('assessment_type','').split('@@')[0])
            I_CONTEXT_ID = request.get('I_CONTEXT_ID', '')
            sel_attr='<select name="assessment_name'+str(I_CONTEXT_ID)+'" class="mandatorychk">\
                               <option value="">---Select One---</option>'
            if i_assmnt_type:
                result_set = self.Assessment.Model.getAssessments(assmnt_title='',\
                                                                  assmnt_type=i_assmnt_type,\
                                                                  assmnt_status='Published',\
                                                                  assmnt_temp_idn='',\
                                                                  mod_type='ace',\
                                                                  from_rec='',\
                                                                  to_rec='').dictionaries()
                if result_set:
                    for res_value in result_set:
                        sel_attr+='<option value='+str(res_value['ACE_TITLE_IDN'])+"@@"+str(res_value['ACE_TEMPLATE_IDN'])+"@@"+str(res_value['ACE_VERSION_NO'])+"@@"+str(res_value['ACE_TITLE_DESCRIPTION'])+'>'+str(res_value['ACE_TITLE_DESCRIPTION'])+'</option>'
            sel_attr+='</select>'
            return sel_attr
        else:
            i_assmnt_type = i_assmnt_type.split('@@')[0]
            result_set = self.Assessment.Model.getAssessments(assmnt_title='',\
                                                              assmnt_type=i_assmnt_type,\
                                                              assmnt_status='Published',\
                                                              assmnt_temp_idn='',\
                                                              mod_type='ace',\
                                                              from_rec='',\
                                                              to_rec='').dictionaries()
            return result_set

    def getAssessmentRuleElifDetails(self):
        """
        @description : This method is used to fill rule elif contents in the respective block
        @return : return to rule else if page.
        """
        request = self.REQUEST        
        tabCount = request.get('elifblkcount', '')
        I_CONTEXT_ID = request.get('I_CONTEXT_ID', '')
        form_name = request.get('form_name', '')
        header_type = ''
        if request.has_key('header_type'):
            header_type = request['header_type']
        header = self.ZeUI.getHeader(header_type)
        footer = self.ZeUI.getFooter(header_type)
        dtml_document = getattr(self.views, 'assessment_rule_elseif_page')
        return header+dtml_document(self.views, REQUEST=self.REQUEST,
                                    tabCount=tabCount,
                                    I_CONTEXT_ID=I_CONTEXT_ID,
                                    form_name=form_name)+footer

    def addAssessmentRuleSet(self):
        """
        @description : This method is used to add rule
        @return : This method returns Rule edit Page after adding a new rule
        """
        request = self.REQUEST
        try:
            user_id = int(self.cms.ZeUser.Model.getLoggedinUserIdn())
        except:
            user_id = 3
        pkg_title = request.get('assessment_rule_set','').strip()
        sre_rule_ctgy_idn = request.get('business_process','')
        pkg_type = request.get('ruleset_type','')
        pkg_description = request.get('ruleset_description','').strip()
        sre_event_name_idn = request.get('event_title','')
        sre_rule_src_idn = self.getRuleSetSource(rule_src_cd='assessment').dictionaries()[0]['SRC_IDN']
        ruleset_type = request.get('ruleset_type','')
        rules_set_execution_type = request.get('rules_set_execution_type','')
        I_CONTEXT_ID = request.get('I_CONTEXT_ID', '')
        assessment_template = request.get('assessment_id_hidden').split('@@')
        assessment_type = request.get('assessment_type_hidden','').split('@@')
        version_no = request.get('version_no_hidden',0)
        criteria_total_count = int(request.get('criteria_total_count', '0'))
        action_total_count = int(request.get('action_total_count', '0'))
        #assessment_id = int(assessment_name.split('$$')[0])
        ruleid_lst = []
        elifBlock_count = int(request.get('elifDivCount','0'))
        ext_pkg_cd = 'RULESET'+get_base_external_cd(self)
        pkg_id = self.Sentinel.SentinelModel.insertAssessmentRuleSet(pkg_title=pkg_title,\
                                                                     pkg_description=pkg_description,\
                                                                     pkg_type=pkg_type,\
                                                                     sre_rule_ctgy_idn=sre_rule_ctgy_idn,\
                                                                     sre_event_name_idn=sre_event_name_idn,\
                                                                     user_idn=user_id,\
                                                                     entity_active='Y',\
                                                                     sre_rule_src_idn=int(sre_rule_src_idn),\
                                                                     assmnt_template_idn=int(assessment_template[1]),
                                                                     rules_set_execution_type=rules_set_execution_type,
                                                                     ext_pkg_cd=ext_pkg_cd
                                                                     )


        if pkg_id:
            pkg_id=pkg_id[0][0]
            for block in range(0,elifBlock_count+1):
                ext_rule_cd = 'RULE'+get_base_external_cd(self)
                rule_title = str(assessment_template[3])+'-'+str(assessment_type[1])+'-'+str(block) + '_' + ext_rule_cd
                rule_id = self.Sentinel.SentinelModel.insertAssessmentRule(rule_title=rule_title,\
                                                                           sre_rule_ctgy_idn=sre_rule_ctgy_idn,\
                                                                           ruleset_type=ruleset_type,\
                                                                           rule_execution_type=rules_set_execution_type,
                                                                           sre_event_name_idn=sre_event_name_idn,\
                                                                           user_idn=user_id,\
                                                                           entity_active='Y',\
                                                                           sre_rule_src_idn=int(sre_rule_src_idn),\
                                                                           assmnt_template_idn=int(assessment_template[1]),
                                                                           ext_rule_cd=ext_rule_cd
                                                                           )
                if rule_id:
                    rule_id=rule_id[0][0]
                    ruleid_lst.append(rule_id) #append the rule_id
                    self.Sentinel.SentinelModel.insertAttachRule(pkg_id=int(pkg_id),\
                                                                 rule_id=int(rule_id),\
                                                                 priority=block,\
                                                                 user_idn=user_id,\
                                                                 idpool_label_idn=None
                                                                 )
            #Assessment Rule Action inserting
            delete_count = int(request.get('delete_count',0))
            total_block = elifBlock_count + delete_count + 1
            pos = 0
            for i in range(0,int(total_block)):
                count_blk = 0
                for j in range(0,int(action_total_count)):
                    if_qstn = request.get('action_id'+str(i)+'_if_'+str(j),'')
                    if request.has_key('action_id'+str(i)+'_if_'+str(j)) and if_qstn:
                        rule_id = ruleid_lst[pos]
                        count_blk = 1
                        self.Sentinel.SentinelModel.insertRuleAction(rule_id=int(rule_id),
                                                                     action_id=if_qstn,
                                                                     user_id=user_id,
                                                                     priority=j,
                                                                     exec_group=0
                                                                     )
                if count_blk:
                    pos = pos + 1

            #Assessment Rule Action inserting
            pos = 0
            for i in range(0,int(total_block)):
                count_blk = 0
                for j in range(0,int(action_total_count)):
                    else_qstn = request.get('action_id'+str(i)+'_else_'+str(j),'')
                    if request.has_key('action_id'+str(i)+'_if_'+str(j)):
                        rule_id = ruleid_lst[pos]
                        count_blk = 1
                        if else_qstn:
                            self.Sentinel.SentinelModel.insertRuleAction(rule_id=int(rule_id),
                                                                         action_id=else_qstn,
                                                                         user_id=user_id,
                                                                         priority=j,
                                                                         exec_group=1
                                                                         )
                if count_blk:
                    pos = pos + 1

            #Assessment Rule criteria inserting
            pos = 0
            for i in range(0,int(total_block)):
                count_blk = 0
                for j in range(0,int(criteria_total_count)):
                    question = request.get('question'+str(i)+'_'+str(j),'')
                    if request.has_key('question'+str(i)+'_'+str(j)) and question:
                        rule_id = ruleid_lst[pos]
                        count_blk = 1
                        prefix_op = request.get('prefix_op'+str(i)+'_'+str(j),'')
                        qst_title = request.get('question'+str(i)+'_'+str(j),'').split('@@')[1]
                        sre_entity_idn = request.get('question'+str(i)+'_'+str(j),'').split('@@')[2]
                        binary_op = request.get('binary_op'+str(i)+'_'+str(j),'')
                        val = request.get('qval'+str(i)+'_'+str(j),'')
                        suffix_op = request.get('suffix_op'+str(i)+'_'+str(j),'')
                        priority = j - 1
                        criteria_type = 'TEST_AGAINST_VALUE'
                        if qst_title:
                            ext_criteria_cd = "CRITERIA-"+get_base_external_cd(self)
                            criteria_title = qst_title + '_' + ext_criteria_cd
                            criteria_id = self.Sentinel.SentinelModel.insertAssessmentCriteria(criteria_title=criteria_title,\
                                                                                               criteria_description=qst_title,\
                                                                                               binary_op=binary_op,\
                                                                                               value=val,\
                                                                                               criteria_type=criteria_type,\
                                                                                               user_idn=user_id,\
                                                                                               sre_entity_idn1=sre_entity_idn,\
                                                                                               entity_active='Y',
                                                                                               ext_criteria_cd=ext_criteria_cd
                                                                                               )
                            if criteria_id:
                                criteria_id=criteria_id[0][0]
                                self.Sentinel.SentinelModel.addCriteriasForRule(rule_id=int(rule_id),\
                                                                                prefix_op=prefix_op,\
                                                                                suffix_op=suffix_op,\
                                                                                criteria_ids=int(criteria_id),\
                                                                                priority=priority,\
                                                                                user_id=user_id,\
                                                                                exec_group=0
                                                                                )
                if count_blk:
                    pos = pos + 1

        return'%s~~%s~~%s~~%s~~%s'%(pkg_id,request.get('assessment_id_hidden'),request.get('assessment_type_hidden',''),version_no,sre_rule_src_idn)

    def showAssessmentRuleSetUpdatePage(self):
        """
        @description : This method is used to show rule edit page.
        @return : return to show rule edit page.
        """
        request = self.REQUEST
        rule_set_id = request.get('pkg_id','')
        ruleid_lst = self.Sentinel.SentinelModel.getRuleSetRule(rule_set_id=rule_set_id).dictionaries()
        rule_id = []
        current_rule_idn = ''
        for idn in ruleid_lst:
            rule_id.append(int(idn['SRE_RULE_IDN']))
            current_rule_idn += str(idn['SRE_RULE_IDN']) + '@@'
        I_CONTEXT_ID = request.get('I_CONTEXT_ID','')
        entity_active = request.get('entity_active','')
        came_from = request.get('came_from','')
        if came_from == 'search_ruleset':
            assmnt_template_idn = request.get('assmt_template_idn',0)
            result_set = self.Assessment.Model.getAssessments(assmnt_title='',\
                                                              assmnt_type='',\
                                                              assmnt_status='Published',\
                                                              assmnt_temp_idn=assmnt_template_idn,\
                                                              mod_type='ace',\
                                                              from_rec='',\
                                                              to_rec='').dictionaries()
            if result_set:
                assessment_id = str(result_set[0]['ACE_TITLE_IDN'])+"@@"+\
                              str(result_set[0]['ACE_TEMPLATE_IDN'])+"@@"+\
                              str(result_set[0]['ACE_VERSION_NO'])+"@@"+\
                              str(result_set[0]['ACE_TITLE_DESCRIPTION'])
                assessment_type = str(result_set[0]['ACE_TYPE_IDN'])+"@@"+str(result_set[0]['ACE_TYPE'])
                version_no = str(result_set[0]['ACE_VERSION_NO'])
            else:
                # If there is no assessment resultset we are redirecting to view only page and displaying a warning msg.
                checked_values = request.get('checked_values','')
                request.set('warning','No corresponding published assessment found. Please deactivate rule set and create new one')
                header = self.ZeUI.getHeader()
                footer = self.ZeUI.getFooter()
                dtml_document = getattr(self.views, 'rule_set_view')
                next_page = header+dtml_document(self.views,
                                                 request=request,
                                                 pkg_id=rule_set_id,
                                                 I_CONTEXT_ID = I_CONTEXT_ID,
                                                 checked_values = checked_values
                                                 )+footer
                return next_page

        else:
            assessment_id = request.get('assessment_id_hidden','')
            assmnt_template_idn = assessment_id.split('@@')[1]
            assessment_type = request.get('assessment_type_hidden','')
            version_no = request.get('version_no_hidden',0)
            rule_source_idn = request.get('rule_source_hidden',0)

        criteria_count = 0
        action_count = 0
        qst_title = self.getQuestionTitle(assessment_template_idn=int(assmnt_template_idn))
        criteria_result = self.Sentinel.SentinelModel.getAssmntCriteriasForRule(
            rule_id = str(rule_id)[1:-1],
            pkg_id = rule_set_id).dictionaries()# get criteria results
        # seperate results based on exec group
        for cri in criteria_result:
            cri['CRITERIA_TITLE'] = qst_title
            if cri['RULE_PRIORITY'] == 0:
                cri['block'] = 'if'
            else:
                cri['block'] = 'elseif'+str(cri['RULE_PRIORITY'])
        action_result = []
        for j in range(0,len(rule_id)):
            actions = self.Sentinel.SentinelModel.getRuleActionMasterDetails(int(rule_id[j])).dictionaries()# get action results
            for act in actions:
                if act['EXEC_GROUP'] == 0:
                    act['block'] = 'ifaction'+str(j)
                else:
                    act['block'] = 'elseaction'+str(j)
                action_result.append(act)
        block_count = len(rule_id)
        assmt_ruleset_details = self.Sentinel.SentinelModel.getAssessmentDetailsForRulesetId(\
            ruleset_id=int(rule_set_id),package_enabled=entity_active).dictionaries()
        rule_source_idn = assmt_ruleset_details[0]['SRE_RULE_SRC_IDN']
        src = request.get('src','')
        msg_code = {'addAssessmentRuleSet':'792','updateAssessmentRuleSet':'795'}
        if src:
            request.set('info_alert', self.ZeUtil.getJivaMsg(msg_code = msg_code[src]))
        header = self.ZeUI.getHeader()
        footer = self.ZeUI.getFooter()
        dtml_document = getattr(self.views, 'assessment_rule_set_edit')
        next_page = header+dtml_document(self.views,
                                         request=request,
                                         pkg_result=assmt_ruleset_details,
                                         block_count=block_count,
                                         criteria_result=criteria_result,
                                         action_result=action_result,
                                         criteria_count=0,
                                         action_count=0,
                                         I_CONTEXT_ID=I_CONTEXT_ID,
                                         assessment_type_id=assessment_type,
                                         assessment_id=assessment_id,
                                         version_no=version_no,
                                         rule_source_idn=rule_source_idn,
                                         rule_set_id=rule_set_id,
                                         rule_id=current_rule_idn,
                                         entity_active=entity_active)+footer
        return next_page

    def updateAssessmentRuleSet(self):
        """"
        Update Assessment Rule Set
        """
        request = self.REQUEST
        try:
            user_idn = int(self.cms.ZeUser.Model.getLoggedinUserIdn())
        except:
            user_idn = 3
        rule_set_title = request.get('rule_set_title','').strip()
        rule_ctgy_id = request.get('business_process','')
        rule_set_description = request.get('rule_set_description','').strip()
        event_type = request.get('event_title','')
        rule_set_type = request.get('rule_set_type','')
        rules_set_execution_type = request.get('rules_set_execution_type','')
        pkg_id = int(request.get('pkg_id',0))
        assessment_template = request.get('assessment_id_hidden','').split('@@')
        assessment_type = request.get('assessment_type_hidden','').split('@@')
        rule_source_idn = request.get('rule_source_hidden',0)
        I_CONTEXT_ID = request.get('I_CONTEXT_ID', '')
        criteria_total_count = int(request.get('criteria_total_count', '0'))
        action_total_count = int(request.get('action_total_count', '0'))

        ruleid_lst = request.get('ruleid_lst','')[:-2].split('@@')
        rule_id = []
        for idn in ruleid_lst:
            rule_id.append(int(idn.strip()))
        elifBlock_count = int(request.get('elifDivCount','0'))
        self.Sentinel.SentinelModel.updateRuleSet(\
            rule_set_title,
            rule_set_description,
            rule_set_type,
            rules_set_execution_type,
            rule_ctgy_id,
            event_type,
            rule_source_idn,
            user_idn,
            pkg_id
        )

        self.Sentinel.SentinelModel.InactiveRulePkg(pkg_id)
        self.Sentinel.SentinelModel.deactivateAssessmentRule(str(rule_id)[1:-1],user_idn)

        rule_criteria_id = self.Sentinel.SentinelModel.getAssessmentCriteria(str(rule_id)[1:-1]).dictionaries()
        criteria_id = []
        for idn in rule_criteria_id:
            criteria_id.append(int(idn['CRITERIA_IDN']))

        if criteria_id:
            self.Sentinel.SentinelModel.deactivateAssessmentCriteria(str(rule_id)[1:-1],user_idn)

        for idn in rule_id:
            self.Sentinel.SentinelModel.deActivateAllActionsForRule(idn)
            self.Sentinel.SentinelModel.deActivateAllCriteriaForRule(idn)

        ruleid_lst = []
        for block in range(0,elifBlock_count+1):
            ext_rule_cd = 'RULE'+get_base_external_cd(self)
            rule_title = str(assessment_template[3])+'-'+str(assessment_type[1])+'-'+str(block) + '_' + ext_rule_cd
            rule_id = self.Sentinel.SentinelModel.insertAssessmentRule(rule_title=rule_title,\
                                                                       sre_rule_ctgy_idn=rule_ctgy_id,\
                                                                       ruleset_type=rule_set_type,\
                                                                       rule_execution_type=rules_set_execution_type,
                                                                       sre_event_name_idn=event_type,\
                                                                       user_idn=user_idn,\
                                                                       entity_active='Y',\
                                                                       sre_rule_src_idn=rule_source_idn,\
                                                                       assmnt_template_idn=int(assessment_template[1]),
                                                                       ext_rule_cd=ext_rule_cd
                                                                       )
            if rule_id:
                rule_id=rule_id[0][0]
                ruleid_lst.append(rule_id) #append the rule_id
                self.Sentinel.SentinelModel.insertAttachRule(pkg_id=pkg_id,\
                                                             rule_id=int(rule_id),\
                                                             priority=block,\
                                                             user_idn=user_idn,\
                                                             idpool_label_idn=None
                                                             )
        #Assessment Rule Action inserting
        delete_count = int(request.get('delete_count',0))
        total_block = elifBlock_count + delete_count + 1
        pos = 0
        for i in range(0,int(total_block)):
            count_blk = 0
            for j in range(0,int(action_total_count)):
                if_qstn = request.get('action_id'+str(i)+'_if_'+str(j),'')
                if request.has_key('action_id'+str(i)+'_if_'+str(j)) and if_qstn:
                    rule_id = ruleid_lst[pos]
                    count_blk = 1
                    self.Sentinel.SentinelModel.insertRuleAction(rule_id=int(rule_id),
                                                                 action_id=if_qstn,
                                                                 user_id=user_idn,
                                                                 priority=j,
                                                                 exec_group=0
                                                                 )
            if count_blk:
                pos = pos + 1

        #Assessment Rule Action inserting
        pos = 0
        for i in range(0,int(total_block)):
            count_blk = 0
            for j in range(0,int(action_total_count)):
                else_qstn = request.get('action_id'+str(i)+'_else_'+str(j),'')
                if request.has_key('action_id'+str(i)+'_if_'+str(j)):
                    rule_id = ruleid_lst[pos]
                    count_blk = 1
                    if else_qstn:
                        self.Sentinel.SentinelModel.insertRuleAction(rule_id=int(rule_id),
                                                                     action_id=else_qstn,
                                                                     user_id=user_idn,
                                                                     priority=j,
                                                                     exec_group=1
                                                                     )
            if count_blk:
                pos = pos + 1

        #Assessment Rule criteria inserting
        pos = 0
        for i in range(0,int(total_block)):
            count_blk = 0
            for j in range(0,int(criteria_total_count)):
                question = request.get('question'+str(i)+'_'+str(j),'')
                if request.has_key('question'+str(i)+'_'+str(j)) and question:
                    rule_id = ruleid_lst[pos]
                    count_blk = 1
                    prefix_op = request.get('prefix_op'+str(i)+'_'+str(j),'')
                    qst_title = request.get('question'+str(i)+'_'+str(j),'').split('@@')[1]
                    sre_entity_idn = request.get('question'+str(i)+'_'+str(j),'').split('@@')[2]
                    binary_op = request.get('binary_op'+str(i)+'_'+str(j),'')
                    val = request.get('qval'+str(i)+'_'+str(j),'')
                    suffix_op = request.get('suffix_op'+str(i)+'_'+str(j),'')
                    priority = j - 1
                    criteria_type = 'TEST_AGAINST_VALUE'
                    if qst_title:
                        ext_criteria_cd = "CRITERIA-"+get_base_external_cd(self)
                        criteria_title = qst_title + '_' + ext_criteria_cd
                        criteria_id = self.Sentinel.SentinelModel.insertAssessmentCriteria(criteria_title=criteria_title,\
                                                                                           criteria_description=qst_title,\
                                                                                           binary_op=binary_op,\
                                                                                           value=val,\
                                                                                           criteria_type=criteria_type,\
                                                                                           user_idn=user_idn,\
                                                                                           sre_entity_idn1=sre_entity_idn,\
                                                                                           entity_active='Y',
                                                                                           ext_criteria_cd=ext_criteria_cd
                                                                                           )
                        if criteria_id:
                            criteria_id=criteria_id[0][0]
                            self.Sentinel.SentinelModel.addCriteriasForRule(rule_id=int(rule_id),\
                                                                            prefix_op=prefix_op,\
                                                                            suffix_op=suffix_op,\
                                                                            criteria_ids=int(criteria_id),\
                                                                            priority=priority,\
                                                                            user_id=user_idn,\
                                                                            exec_group=0
                                                                            )
            if count_blk:
                pos = pos + 1

        request.set('src','updateAssessmentRuleSet')
        return self.showAssessmentRuleSetUpdatePage()

    def showExportAssessmentRuleSetSearchPage(self):
        """
        @description : This method is used to show export rule set search page.
        @return : returns to export rule set search page.
        """
        request = self.REQUEST
        keywords_rst = self.Sentinel.SentinelModel.getKeywords()
        header_type = ''
        if request.has_key('header_type'):
            header_type = request['header_type']
        header = self.ZeUI.getHeader(header_type)
        footer = self.ZeUI.getFooter(header_type)
        dtml_document = getattr(self.views, 'export_assessment_ruleset_search')
        next_page = header+dtml_document(self.views, REQUEST=request,keywords_rst=keywords_rst)+footer
        return next_page

    def getAssessmentRulesSetResultPage(self):
        """
        @description : This method used to get rule set result page.
        @return : return to rule set result page.
        """
        request = self.REQUEST
        rule_set_title = request.get('rule_set_title','')
        event_id = request.get('event_title','')
        rule_title=request.get('rule_title','')
        package_enabled = request.get('filter_enabled','Y')
        package_id = request.get('package_id','')
        rule_src_idn = request.get('src_idn','')
        checked_chkbox = request.get('checked_chkbox','')
        noResultMsg=self.ZeUtil.getJivaMsg(msg_code='627')
        status = request.get('status','')
        if status:
            msg_code = {'activate':'017','deactivate':'016'}
            request.set('info_alert', self.ZeUtil.getJivaMsg(msg_code = msg_code[status.lower()]))
        header_type = ''
        if request.has_key('header_type'):
            header_type = request['header_type']
        header = self.ZeUI.getHeader(header_type)
        footer = self.ZeUI.getFooter(header_type)
        # pagination
        page_info = self.getPageDetails()

        next_count = self.Sentinel.SentinelModel.\
                   getRuleSetCount(\
                       package_enabled=package_enabled,
                       rule_set_title=rule_set_title,
                       event_id=event_id,
                       rule_title=rule_title,
                       rule_src_idn=rule_src_idn
                       )[0][0]

        package_details_recordset = self.Sentinel.\
                                  SentinelModel.selectRuleSetDetails(\
                                      package_enabled=package_enabled,
                                      rule_set_title=rule_set_title,
                                      event_id=event_id,
                                      rule_title=rule_title,
                                      rule_src_idn=rule_src_idn,
                                      query_from=page_info['I_START_REC_NO'],
                                      query_to=page_info['I_END_REC_NO']
                                  )
        package_details_list = package_details_recordset.dictionaries()
        for eachpackageRecord in package_details_list:

            eventType = self.Sentinel.SentinelModel.\
                      getCodeEventDetails(\
                          eachpackageRecord['EVENT_TITLE']
                          )[0]['EVENT_DESCRIPTION']

            ruleCategory = self.Sentinel.SentinelModel.\
                         getCodeRuleCategory(\
                             eachpackageRecord['RULE_CTGY']
                             )[0]['CTGY_CD']

            eachpackageRecord['EVENT_TYPE']=eventType
            eachpackageRecord['RULE_CTGY']=ruleCategory

        dtml_document = getattr(self.views,'export_assessment_ruleset_result_page')
        return header+dtml_document(self.views,\
                                    REQUEST=request,
                                    new_rule_set_list=package_details_list,
                                    rule_set_title=rule_set_title,
                                    event_id=event_id,
                                    rule_title=rule_title,
                                    filter_enabled = package_enabled,
                                    total_rec = next_count,
                                    I_CUR_PG=page_info['I_CUR_PAGE'],
                                    package_id=package_id,
                                    checked_chkbox=checked_chkbox,
                                    rule_src_idn=rule_src_idn,
                                    noResultMsg=noResultMsg
                                    )+footer

    def showAssessmentRuleSetExportToXlPage(self):
        """
        @method showAssessmentRulesetExportToXlPage
        @return This function returns,
        result_set (result set of assessment ruleset details) to xl dtml page
        """
        request = self.REQUEST
        ruleset_id = request.get('cid','')
        rule_set_title = request.get('rule_set_title','')
        event_id = request.get('event_id','')
        rule_title=request.get('rule_title','')
        package_enabled = request.get('filter_enabled','Y')
        src_id = request.get('src_idn', '')
        ace_template_ids = set([])
        associated_rule_set = set([])
        associated_rules = set([])

        assmnt_ruleset_result_set = self.Sentinel.SentinelModel.getAssessmentDetailsForRulesetId(ruleset_id=ruleset_id,
                                                                                                 rule_set_title=rule_set_title,
                                                                                                 event_id=event_id,
                                                                                                 rule_title=rule_title,
                                                                                                 package_enabled=package_enabled,
                                                                                                 rule_src_idn=src_id)
        assmnt_ruleset_details = assmnt_ruleset_result_set.dictionaries()
        # If no matching rule records found, raise error
        if not assmnt_ruleset_details:
            raise Exception("No rule set details found")

        for each_rule_set in assmnt_ruleset_details:
            ace_template_ids.add(each_rule_set['ACE_TEMPLATE_IDN'])
            rule_set_id = each_rule_set['PKG_ID']
            associated_rule_set.add(rule_set_id)
            rule_details = self.Sentinel.SentinelModel.showRuleDetailsForPackageId(rule_set_id, entity_active='Y').dictionaries()
            associated_rules.update([each_rule['SRE_RULE_IDN'] for each_rule in rule_details])

        criteria_results = self.get_rule_criteria_for_export(rule_id=list(associated_rules))
        # If no matching rule records found, raise error
        if not criteria_results:
            raise Exception("No associated criteria details for given rule set found")

        action_results = self.get_rule_actions_for_export(rule_id=list(associated_rules))
        # If no matching rule records found, raise error
        if not action_results:
            raise Exception("No associated action details for given rule set found")

        excel_object_url = assessment_rule_set_export(self, criteria_results, action_results, assmnt_ruleset_details, ace_template_ids, list(associated_rule_set))
         
        return request.RESPONSE.redirect(excel_object_url)
        
        # The below commented section to be deleted when 
        # export export functionality has been approved
        #=======================================================================
        # stylestr = self.Reports.Controller.getExcelStyleSheet(view_name='assessment_ruleset_installation_template.xls')
        # dtml_document = getattr(self.views, 'export_assessment_ruleset')
        # return stylestr + dtml_document(self.views,
        #                                REQUEST=request,
        #                                action_results=action_results,
        #                                ruleset_id = ruleset_id,
        #                                src_id = src_id,
        #                                noResultMsg=noResultMsg)
        #=======================================================================

    def showAssessmentImportRuleSetPage(self):
        """
        @description : This method is used to show import rule set page.
        @return : return to show import rule set page
        """
        request = self.REQUEST
        header_type = ''
        if request.has_key('header_type'):
            header_type = request['header_type']
        header = self.ZeUI.getHeader(header_type)
        footer = self.ZeUI.getFooter(header_type)
        dtml_document = getattr(self.views, 'import_assessment_ruleset_page')
        return header+dtml_document(self.views, REQUEST=request)+footer

    def disableDecTableCriteriaRow(self):
        """
        Disable Decision Table Criteria Row
        """
        request = self.REQUEST
        try:
            user_id = int(self.cms.ZeUser.Model.getLoggedinUserIdn())
        except:
            user_id = 3
        criteria_id = request.get('criteriaId','')
        if criteria_id:
            self.Sentinel.SentinelModel.disableDecTableCriteriaRow(criteria_id = criteria_id,
                                                                   user_id=user_id)
        return 1

    def is_advanced_user(self):
        
        """ This method is used to check the user has SENTINEL-ADVANCE role """
        # To be modified later include permission check
        
        user_roles = self.ZeUser.Model.getLoggedInUserRoles(self.REQUEST['AUTHENTICATED_USER'])
        if 'SENTINEL-ADVANCE' in user_roles:
            return 1
               
    def getSentinelLeftMenus(self, comp_name, block_name):
        """
        Generates the left menus corresponding to the 'block_name'
        provided.
        @param block_name: Name of the block in the XML whose tags to
            be generated as Left menus.
        @type block_name: String
        @return: Left menus in a list of tuples. Each tuple containing
            URL as a first value  and the title as a second value.
        """
        menu_list = []
        base_url = self.ZeUtil.getBaseURL()
        link_attrs = {}
        user_roles = set(self.ZeUser.Model.getLoggedInUserRoles(self.REQUEST['AUTHENTICATED_USER'])) 
        xml_obj = self.ZeUI.xmlFiles.jivaLeftNavigation.documentElement.getElementsByTagName(comp_name)
        items_list = xml_obj.documentElement.getElementsByTagName(block_name)
        heading = items_list[0].getAttribute('title')
        if items_list[0].getAttribute('show') == 'Y':
            for each in items_list[0].getElementsByTagName("item"):
                show = each.attributes["show"].value
                config_role = each.attributes["roles"].value
                config_role = set(config_role.split(","))
                is_visible = config_role.intersection(user_roles)
                if is_visible and show == 'Y':
                    panel = each.attributes["panel"].value
                    try:
                        panel_prefix = each.attributes["panel_id"].value
                    except:
                        panel_prefix = ''
                    db_lookup = each.attributes["db_lookup"].value
                    node_value = self.ZeUtil.encode(each.firstChild.nodeValue.strip())                    
                    url = base_url + '/' + node_value
                    if db_lookup == 'Y':
                        db_url = each.attributes["db_url"].value
                        fun_mtd = eval('self.'+str(db_url.replace('/','.')+'()'))
                        for each_url in fun_mtd:
                            link_attrs['url'] = url
                            if block_name == 'event_status':
                                link_attrs['menu_title'] = each_url['NAME']
                                link_attrs['menu_desc'] = each_url['NAME']
                                panel_title = '(Event) '+str(each_url['EVENT_STATUS'])
                                param = 'event_status='+str(each_url['EVENT_STATUS'])
                                panel_id = str(each_url['EVENT_STATUS']).replace(' ','').strip()

                            elif block_name == 'events':
                                link_attrs['menu_title'] = each_url['NAME']
                                link_attrs['menu_desc'] = each_url['NAME']
                                panel_title = '(Event) '+str(each_url['NAME'])
                                param = 'event_title='+str(each_url['CD'])
                                panel_id = str(each_url['CD'])

                            elif block_name == 'actions':
                                link_attrs['menu_title'] = each_url[0]
                                link_attrs['menu_desc'] = each_url[0]
                                panel_title = '(Action) '+str(each_url[0])
                                param = 'action_script='+each_url[0]
                                panel_id = str(each_url[1])

                            elif block_name in ('rule_business_process','ruleset_business_process'):
                                link_attrs['menu_title'] = each_url['CTGY_CD']
                                panel_title = '('+str(heading)+') '+str(each_url[0])
                                link_attrs['menu_desc'] = each_url['CTGY_CD']
                                param = 'rule_category='+str(each_url['IDN'])
                                panel_id = str(each_url['IDN'])

                            else:    
                                link_attrs['menu_title'] = each_url
                                link_attrs['menu_desc'] = each_url
                                param = panel_id = ''


                            link_attrs['heading'] = heading
                            if panel == 'Y':
                                link_attrs['menu_click'] = '$SENTINEL.openSentinelPanel(\''+panel_title+\
                                          '\',\'window\',\''+\
                                          url+'\',\''+\
                                          param+'\',\''+\
                                          panel_prefix+panel_id+'\')'                   
                            menu_list.append(link_attrs)
                            link_attrs = {}

                    else:
                        menu_title = self.ZeUtil.encode(each.attributes["title"].value)
                        menu_desc = self.ZeUtil.encode(each.attributes["desc"].value)
                        if panel == 'Y':
                            link_attrs['menu_click'] = '$SENTINEL.openSentinelPanel(\''+menu_title+\
                                      '\',\'window\',\''+\
                                      url+\
                                      '\',\''+\
                                      ''+\
                                      '\',\''+\
                                      panel_prefix+\
                                      '\')'                    
                        else:
                            link_attrs['menu_click'] = '$PANELS.hideAllEpisodePanels();$JIVA.changeJivaContent(\''+\
                                      url+'\',\'sub\')'
                        link_attrs['url'] = url
                        link_attrs['menu_title'] = menu_title
                        link_attrs['heading'] = heading
                        link_attrs['menu_desc'] = menu_desc
                        menu_list.append(link_attrs)
                        link_attrs = {}

        return menu_list     
    
    def getScreenNames(self):
        """
        @description : This method is used to return screen names
        """
        screen_names = constants.SCREEN_NAMES
        return screen_names

    def getFormFieldNames(self):
        """
        @description : This method is used to return form field names
        """
        column_names = constants.COLUMN_NAMES
        return column_names

    def getSisMsgStatus(self):
        """
        @description : Method to get Sis Message Status defined in sentinel_constants
        @return : This function returns get Sis Message Status defined in sentinel_constants.
        """
        return constants.SIS_MSG_STATUS

    def showValidationRuleAddPage(self):
        """
        @description : This method is used to show rule add page.
        @return : return to rule add page.
        """
        request = self.REQUEST
        output_entity = constants.OUTPUT_ENTITY
        I_CONTEXT_ID = request.get('I_CONTEXT_ID','')
        dtml_document = getattr(self.views, 'validation_rule_add_page')
        header = self.ZeUI.getHeader('Add Validation Rule')
        footer = self.ZeUI.getFooter()
        next_page = header+dtml_document(self.views,
            request=request,
            I_CONTEXT_ID = I_CONTEXT_ID,
            output_entity = output_entity)+footer
        return next_page

    def triggerSentinelEventForValidation(self):
        """
        Used to log event from JS

         This method is to call sentinel validation rule and returns json response.
        format = {"result": {"response": 0,'Type':'S','Msg':'Alert the user'}}
        {response:1} --> Validation failed. Alert message to user
        {response:0} --> Validation passed, submit the form
        {'Type':'S'} --> Type of alert JS OK Cancel of Alert.
        {'Msg':'Alert the user'} --> Custom alert messaged returned from sentinel.
        
        """
        request = self.REQUEST
        event_name = request['event_name']
        event_parameter_dict = {}
        event_parameter_dict['I_CLAIMANT_IDN'] = request.get('I_CLAIMANT_IDN', 0) or 0
        event_parameter_dict['I_ENCOUNTER_IDN'] = request.get('I_ENCOUNTER_IDN', 0) or 0
        event_parameter_dict['I_ENC_TYPE_CD'] = request.get('I_ENC_TYPE_CD', '-') or '-'
        action = request.get('ACTION', '')
        default_dt = '10/10/1900'
        if action == 'attach' and request.get('prv_idn', 0):
            prv_idn = request.get('prv_idn', 0)
            prv_role = request.get('prv_role', '')
            event_parameter_dict['I_PRV_IDN'] = prv_idn
            event_parameter_dict['I_PRV_ROLE'] = prv_role
        elif action == 'editRole' and request.get('I_PRV_IDN', 0):
            prv_idn = request.get('I_PRV_IDN', 0)
            prv_role = request.get('I_PRV_ROLE_CD', '')
            event_parameter_dict['I_PRV_IDN'] = prv_idn
            event_parameter_dict['I_PRV_ROLE'] = prv_role
        elif action == 'activate' and request.get('I_PRV_IDN', 0):
            prv_idn = request.get('I_PRV_IDN', 0)
            prv_role = request.get('I_PRV_ROLE', '')
            event_parameter_dict['I_PRV_IDN'] = prv_idn
            event_parameter_dict['I_PRV_ROLE'] = prv_role
        if 'SVC_START_DT' in request:
            if request.get('I_STAY_MSG', '') == 'E':
                event_parameter_dict['I_AUTH_SVC_EXTN_IDN'] = 1
            else:
                event_parameter_dict['I_AUTH_SVC_EXTN_IDN'] = request.get('I_STAY_SERV_EXTN_IDN') or 1
            svc_start_dt_obj = datetime.strptime(request['SVC_START_DT'] or default_dt,'%m/%d/%Y')
            event_parameter_dict['I_SVC_START_DT'] = svc_start_dt_obj.strftime('%Y-%m-%d')
            svc_end_dt_obj = datetime.strptime(request['SVC_END_DT'] or default_dt,'%m/%d/%Y')
            event_parameter_dict['SVC_END_DT'] = svc_end_dt_obj.strftime('%Y-%m-%d')
            if request.get('I_STAY_ADMIT_DT','') == '':
                event_parameter_dict['I_STAY_ADMIT_DT'] = default_dt
            else:  
                svc_admit_dt_obj = datetime.strptime(request['I_STAY_ADMIT_DT'],'%m/%d/%Y')
                event_parameter_dict['I_STAY_ADMIT_DT'] =  svc_admit_dt_obj.strftime('%Y-%m-%d')
        if 'I_SERV_EXTN_IDN' in request:
            if request.get('IS_EXTENSION', '') == 'Y':
                event_parameter_dict['I_AUTH_SVC_EXTN_IDN'] = 1
            else:
                event_parameter_dict['I_AUTH_SVC_EXTN_IDN'] = request.get('I_SERV_EXTN_IDN') or 1
        if 'I_DECISION_CD' in request:
            event_parameter_dict['I_DECISION_CD'] = request['I_DECISION_CD']
        if 'I_DECISION_REASON' in request:
            event_parameter_dict['I_DECISION_REASON'] = request['I_DECISION_REASON']
        if 'I_ENC_GROUP_IDN' in request:
            event_parameter_dict['I_ENC_GROUP_IDN'] = request['I_ENC_GROUP_IDN']
        if 'I_GROUP_IDN' in request:
            event_parameter_dict['I_GROUP_IDN'] = request['I_GROUP_IDN']
        if 'I_VERBAL_NOTIFICATION_DATE' in request :
            notif_dt_obj = datetime.strptime(request['I_VERBAL_NOTIFICATION_DATE'] or default_dt ,'%m/%d/%Y')
            event_parameter_dict['I_VERBAL_NOTIFICATION_DATE'] = notif_dt_obj.strftime('%Y-%m-%d %H:%M:%S') 
        if 'I_INFO_REQUESTED_DATE' in  request:
            info_req_dt_obj = datetime.strptime(request['I_INFO_REQUESTED_DATE'] or default_dt,'%m/%d/%Y')
            event_parameter_dict['I_INFO_REQUESTED_DATE'] = info_req_dt_obj.strftime('%Y-%m-%d %H:%M:%S') 
        if 'I_INFO_RECEIVED_DATE' in  request:
            info_rec_dt_obj = datetime.strptime(request['I_INFO_RECEIVED_DATE'] or default_dt,'%m/%d/%Y')
            event_parameter_dict['I_INFO_RECEIVED_DATE'] = info_rec_dt_obj.strftime('%Y-%m-%d %H:%M:%S') 
        if 'I_EPISODE_CLASS_IDN' in request:
            event_parameter_dict['I_EPISODE_CLASS_IDN'] = request['I_EPISODE_CLASS_IDN']
        if 'I_REASON_FOR_REQUEST' in request:
            event_parameter_dict['I_REASON_FOR_REQUEST'] = request['I_REASON_FOR_REQUEST']
        if 'I_REFERRAL_SOURCE' in request :
            event_parameter_dict['I_REFERRAL_SOURCE'] = request['I_REFERRAL_SOURCE']
        if 'I_ENC_TYPE_CD' in request :
            event_parameter_dict['I_ENC_TYPE_CD'] = request['I_ENC_TYPE_CD']
        if 'I_DISCHARGE_DT' in request:
            discharge_dt_obj = datetime.strptime(request['I_DISCHARGE_DT'],'%m/%d/%Y')
            event_parameter_dict['I_DISCHARGE_DT'] = discharge_dt_obj.strftime('%Y-%m-%d')
        if 'i_dm_type' in request and request['i_dm_type'] :
            event_parameter_dict['i_dm_type'] = request['i_dm_type'].split(',')[1]
        if 'I_STAY_REQ_NO' in request:
            event_parameter_dict['LOS_REQ'] = request['I_STAY_REQ_NO']
        if 'I_REQ_NO' in request:
            event_parameter_dict['LOS_REQ'] = request['I_REQ_NO']
        if 'I_ASGN_NO' in request:
            event_parameter_dict['I_ASGN_NO'] = request['I_ASGN_NO']
        if 'I_STATUS_CD' in request:
            event_parameter_dict['I_ENC_STATUS'] = request['I_STATUS_CD']
        if 'I_TPA_NAME' in request:
            event_parameter_dict['I_TPA_NAME'] = request['I_TPA_NAME']
        if 'I_PAT_GENDER_CD' in request:
            event_parameter_dict['I_PAT_GENDER_CD'] = request['I_PAT_GENDER_CD']
        if 'IS_EXTENSION' in request:
            event_parameter_dict['IS_EXTENSION'] = request['IS_EXTENSION']
        if 'I_UNITS' in request:
            event_parameter_dict['I_UNITS'] = request['I_UNITS']
        if 'I_TIME_PERIOD' in request:
            event_parameter_dict['I_TIME_PERIOD'] = request['I_TIME_PERIOD']
        if 'I_EFF_CVG_DT' in request:
            enc_cvg_eff_dt_obj = datetime.strptime(request['I_EFF_CVG_DT'] or default_dt ,'%m/%d/%Y')
            event_parameter_dict['I_EFF_CVG_DT'] = enc_cvg_eff_dt_obj.strftime('%Y-%m-%d') 
        if 'I_TERM_CVG_DT' in request:
            enc_cvg_term_dt_obj = datetime.strptime(request['I_TERM_CVG_DT'] or default_dt ,'%m/%d/%Y')
            event_parameter_dict['I_TERM_CVG_DT'] = enc_cvg_term_dt_obj.strftime('%Y-%m-%d') 
        if 'I_STAY_EXPECTED_ADMIT_DT' in request:
            expected_admit_dt_obj = datetime.strptime(request['I_STAY_EXPECTED_ADMIT_DT'] or default_dt ,'%m/%d/%Y')
            event_parameter_dict['I_STAY_EXPECTED_ADMIT_DT'] = expected_admit_dt_obj.strftime('%Y-%m-%d') 
        msg = self.Sentinel.SentinelEngine.logEventOnClick(event_name, event_parameter_dict)
        return msg

    def view_label_search_page(self):
        """
        @description: This method is used to show pop window for label search and to select searched results.
        """
        request = self.REQUEST
        I_CONTEXT_ID = request.get('I_CONTEXT_ID','')
        openerFormName = request.get('openerFormName','')
        button_index = request.get('button_index','')
        header_type = request.get('header_type','')
        header = self.ZeUI.getHeader()
        footer = self.ZeUI.getFooter()
        noResultMsg = ''
        if request.has_key('searchres'):
            searchres = request.get('searchres','')
            I_LABEL_NAME = request.get('I_LABEL_NAME','')
            I_LABEL_TYPE = request.get('I_LABEL_TYPE','')
            I_RULE_IDN = request.get('i_rule_idn','')
            page_info = self.getPageDetails()
            if request.get('came_from','') == 'Rule':
                search_result_count = self.Sentinel.SentinelModel.get_Filter_LabelsSearchResultCount(I_LABEL_NAME=I_LABEL_NAME,
                                                                                                     I_LABEL_TYPE=I_LABEL_TYPE).dictionaries()
                search_result = self.Sentinel.SentinelModel.get_Filter_LabelsSearchResult(I_LABEL_NAME=I_LABEL_NAME,
                                                                                          I_LABEL_TYPE=I_LABEL_TYPE,
                                                                                          I_START_REC_NUM=page_info['I_START_REC_NO'],
                                                                                          I_END_REC_NUM=page_info['I_END_REC_NO']).dictionaries()
            elif request.get('came_from','') == 'SearchRule':
                search_result_count = self.Sentinel.SentinelModel.get_search_labels_count_from_codetable(i_label_name=I_LABEL_NAME,
                                                                                                    i_label_type=I_LABEL_TYPE).dictionaries()
                search_result = self.Sentinel.SentinelModel.get_search_labels_from_codetable(i_label_name=I_LABEL_NAME,
                                                                                             i_label_type=I_LABEL_TYPE,
                                                                                             i_start_rec_num=page_info['I_START_REC_NO'],
                                                                                             i_end_rec_num=page_info['I_END_REC_NO']).dictionaries()
            else:
                search_result_count = self.Sentinel.SentinelModel.getLabelsSearchResultCount(I_LABEL_NAME=I_LABEL_NAME,
                                                                                             I_LABEL_TYPE=I_LABEL_TYPE,
                                                                                             I_RULE_IDN=I_RULE_IDN).dictionaries()

                search_result = self.Sentinel.SentinelModel.getLabelsSearchResult(I_LABEL_NAME=I_LABEL_NAME,
                                                                                  I_LABEL_TYPE=I_LABEL_TYPE,
                                                                                  I_RULE_IDN=I_RULE_IDN,
                                                                                  I_START_REC_NUM=page_info['I_START_REC_NO'],
                                                                                  I_END_REC_NUM=page_info['I_END_REC_NO']).dictionaries()

            if search_result_count:
                total_count = search_result_count[0]['NUMBER_RECORD']
            dtml_document = getattr(self.views, 'show_search_labels_result_page')
            noResultMsg = self.ZeUtil.getJivaMsg(msg_code='470')
            dtml_page =  header+dtml_document(self.views,
                                        REQUEST=request,
                                        search_result=search_result,
                                        button_index=button_index,
                                        I_CONTEXT_ID = I_CONTEXT_ID,
                                        openerFormName=openerFormName,
                                        I_CUR_PG=page_info['I_CUR_PAGE'],
                                        total_rec=total_count,
                                        noResultMsg=noResultMsg)+footer
        else:
            dtml_document = getattr(self.views, 'search_labels_page')
            dtml_page = header+dtml_document(self.views,
                                             REQUEST=request,
                                             openerFormName=openerFormName,
                                             button_index=button_index,
                                             I_CONTEXT_ID = I_CONTEXT_ID,
                                             noResultMsg=noResultMsg)+footer
        return dtml_page

InitializeClass(ZeSentinelCtrl)
