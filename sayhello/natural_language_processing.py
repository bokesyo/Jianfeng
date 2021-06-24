from allennlp.predictors.predictor import Predictor
import os
import sys
from sayhello import app
from nltk.stem.wordnet import WordNetLemmatizer
from sayhello.data_read_write import CommonDatabase, CommonFunction
import re
import copy


class OpenInfoPredictor:
    def __init__(self):
        # self.source_tgz = os.path.dirname(app.root_path) + "/sayhello/source/openie-model.2020.03.26.tar.gz"
        self.source_tgz = "https://storage.googleapis.com/allennlp-public-models/openie-model.2020.03.26.tar.gz"
        # print(source_tgz)
        # print("Start Loading")
        self.predictor = Predictor.from_path(self.source_tgz)
        # print("End Loading")

    def query(self, comment):
        output = self.predictor.predict(sentence=comment)
        return output


class EntailmentPredictor:
    def __init__(self):
        # self.source_tgz = os.path.dirname(app.root_path) +
        # "/sayhello/source/decomposable-attention-elmo-2020.04.09.tar.gz"
        self.source_tgz = "https://storage.googleapis.com/allennlp-public-models/decomposable-attention-elmo-2020.04.09.tar.gz"
        self.predictor = Predictor.from_path(self.source_tgz)

    def query(self, pre, hyp):
        output = self.predictor.predict(premise=pre,hypothesis=hyp)['label']
        return output


class NameEntityPredictor:
    def __init__(self):
        # self.source_tgz = os.path.dirname(app.root_path) + "/sayhello/source/ner-elmo.2021-02-12.tar.gz"
        self.source_tgz = "https://storage.googleapis.com/allennlp-public-models/ner-elmo.2021-02-12.tar.gz"
        self.predictor = Predictor.from_path(self.source_tgz)
        print('load finish ner-elmo.2021-02-12.tar.gz')

    def query(self, comment):
        output = self.predictor.predict(sentence=comment)
        return output


class UserPredict:
    def __init__(self, nen_url, func_url, debug_mode=False):
        if not debug_mode:

            self.openInfoEngine = OpenInfoPredictor()
            # self.entailEngine = EntailmentPredictor()
            self.nameEntityEngine = NameEntityPredictor()

        self.commonDB = CommonDatabase(nen_url)
        self.funcDB = CommonFunction(func_url)

        self.verb_database = []
        self.entity_database_per = []
        self.entity_database_org = []
        self.entity_database_loc = []

    def query(self, comment, submit_func=False):
        result_dict = self.openInfoEngine.query(comment)
        # print(result_dict)
        # Determine the principal verb
        tags_0 = []
        n = 0
        for verb_dict in result_dict["verbs"]:
            # print(verb_dict)
            description = verb_dict['description']
            tags = verb_dict['tags']
            # print(tags)
            # print("determine the principal according to the number of 0 tags")
            this = 0
            for i in tags:
                # print(i)
                if i == "O":
                    this += 1
            # print(this)
            tags_0.append(this)
            n += 1
        # print(tags_0)
        # We want the minimal number of tag O
        index_desire = tags_0.index(min(tags_0))
        best_verb_dict = result_dict["verbs"][index_desire]
        # Principal determined!

        self.verb_database.append(best_verb_dict['verb'])

        # To extract the structure of this sentence:
        # Input : '[ARG0: Tom] [V: accuses] [ARG1: Bob] [ARG2: of stealing the money] .'
        string = best_verb_dict['description']
        stack = []
        switch = False
        this_word = ''
        for i in string:
            if i == '[':
                switch = True
            elif i == ']':
                switch = False
                stack.append(this_word)
                this_word = ''
            elif switch:
                this_word += i
            else:
                pass
        string_list = stack
        # Output: ['ARG0: Tom', 'V: accuses', 'ARG1: Bob', 'ARG2: of stealing the money']

        # Convert the verb into standard form.
        verb_standard = WordNetLemmatizer().lemmatize(best_verb_dict['verb'], 'v')

        this_atom_clauses = {'verb': verb_standard, 'neg': False, 'args': None, 'grammar': None,
                             'pure_verb': str(verb_standard)}

        arg_list = {}
        orders = []
        for i in string_list:
            if 'NEG' in i:
                this_atom_clauses['neg'] = True
                orders.append('NEG')
            elif 'ARG' in i:
                ref = i.split(': ')[0]
                obj = i.split(': ')[1]
                orders.append(ref)
                arg_list[ref] = obj
            elif 'V' in i:
                obj = i.split(': ')[1]
                orders.append('V')
        # print(arg_list)
        # print(orders)
        # arg_list = {'ARG0': 'Jerry', 'ARG2': 'Tom', 'ARG1': 'that he wanted to fuck him'}

        this_atom_clauses['args'] = arg_list
        this_atom_clauses['grammar'] = orders
        grammar_type_dict = {}

        final_result = False
        entity_result_list = []

        for i in this_atom_clauses['args'].keys():
            j = this_atom_clauses['args'][i]
            result = self.entity_processing(j)
            entity_result_list.append(result)
            # print(result)
            if result:
                grammar_type_dict[i] = result
                final_result = True
            else:
                grammar_type_dict[i] = False

        this_atom_clauses['args_type'] = grammar_type_dict

        natural_string = ''
        for i in this_atom_clauses['grammar']:
            if 'ARG' in i:
                refer = this_atom_clauses['args_type'][i]
                if refer == "PER":
                    give = '[ a person ]'
                elif refer == "ORG":
                    give = '[ an organization ]'
                elif refer == "LOC":
                    give = '[ a location ]'
                elif not refer:
                    give = this_atom_clauses['args'][i]
            elif i == "V":
                give = this_atom_clauses['pure_verb']
            elif i == "NEG":
                give = ""
            else:
                give = ""
                print('Nothing')
            natural_string = natural_string + " " + give

        # print(natural_string)
        this_atom_clauses['natural_string'] = natural_string
        this_atom_clauses['args_backup'] = this_atom_clauses['args'].copy()

        if not final_result:
            print('This may not be a fact')
            return False

        # suffix
        for i in range(len(arg_list)):
            # print(arg_list)
            if not entity_result_list[i]:
                args_split = arg_list[list(arg_list.keys())[i]].split(' ')
                this_list = [this_atom_clauses['verb']] + args_split
                this_atom_clauses['verb'] = '_'.join(this_list)
                # print(this_atom_clauses_dict['verb'])

        # Remove the False arguments
        new_list = []
        no_false_list = []
        for i in range(len(arg_list)):
            a = arg_list[list(arg_list.keys())[i]]
            b = entity_result_list[i]
            if b:
                no_false_list.append(b)
                new_list.append(a)

        this_atom_clauses['args'] = new_list
        this_atom_clauses['no_false_list'] = no_false_list

        parameter_list = []
        for i in this_atom_clauses['args_type'].keys():
            if this_atom_clauses['args_type'][i]:
                parameter_list.append(i)

        this_atom_clauses['usr_parameter_list'] = parameter_list

        atom_clause = ''
        if this_atom_clauses['neg']:
            atom_clause += '!'
        atom_clause = atom_clause + this_atom_clauses['verb'] + '(' + ','.join(this_atom_clauses['args']) + ')'

        new_usr_parameter_list = []
        for i in this_atom_clauses['usr_parameter_list']:
            new_usr_parameter_list.append(i+'=')
        prefix = this_atom_clauses['verb'] + '('

        this_atom_clauses['prefix'] = prefix
        this_atom_clauses['function'] = atom_clause

        parameter_mln = []
        for i in no_false_list:
            if i == "PER":
                parameter_mln.append("person")
            elif i == "ORG":
                parameter_mln.append("organization")
            elif i == "LOC":
                parameter_mln.append("location")
        function_mln = this_atom_clauses['verb'] + '(' + ','.join(parameter_mln) + ')'
        this_atom_clauses['function_mln'] = function_mln

        print("^^^^^^^^^^^^^^^^^^^")
        print(this_atom_clauses)
        print("^^^^^^^^^^^^^^^^^^^")

        if not submit_func:
            for i in range(len(this_atom_clauses['args'])):
                self.commonDB.add(this_atom_clauses['args'][i], this_atom_clauses['no_false_list'][i])
            self.commonDB.commit()

        # Commit Functions
        self.funcDB.add(this_atom_clauses)
        self.funcDB.commit()
        return atom_clause

    def entity_processing(self, arg):

        tag_result = self.nameEntityEngine.query(arg)['tags']
        print(tag_result)
        result_per = True
        result_org = True
        result_loc = True

        for i in tag_result:
            if 'PER' not in i:
                result_per = False
                break
        if result_per:
            self.entity_database_per.append(arg)
            return 'PER'
        for i in tag_result:
            if 'ORG' not in i:
                result_org = False
                break
        if result_org:
            self.entity_database_org.append(arg)
            return 'ORG'
        for i in tag_result:
            if 'LOC' not in i:
                result_loc = False
                break
        if result_loc:
            self.entity_database_loc.append(arg)
            return 'LOC'
        return False

    def predicate_query(self, data):
        print("-----------------")
        print(data)
        print("-----------------")

        neg = False
        if data[0] == "!":
            neg = True
            data = data.lstrip("!")

        result = None
        for i in self.funcDB.fetch():
            if i['verb'] == data.split('(')[0]:
                result = i
                break

        if result:
            return self.atom_logic_to_nl(result, data, neg)
        else:
            print("no corresponding result...")
            return False

    @staticmethod
    def atom_logic_to_nl(result, data, neg):
        stack = False
        desired = ''
        for i in data:
            if i == ')':
                stack = False
            if stack:
                desired += i
            if i == '(':
                stack = True

        # print(result)

        usr_para = result['usr_parameter_list']
        args_type = result['args_type']
        grammar = result['grammar']
        args = result['args_backup']
        des_list = desired.split(',')

        # print('des_list', des_list)
        # print('usr_para=', usr_para)
        # print('args_type=', args_type)
        # print('args=', args)

        for i in range(len(usr_para)):
            arg_name = usr_para[i]
            args_type[arg_name] = des_list[i]

        # print(args_type)

        nl = ""
        # print("GRAMMAR ===", grammar)
        for i in grammar:
            # print(i)
            if i == "V":
                give = result['pure_verb']
                if neg:
                    give = "not" + " " + give
            elif "ARG" in i:
                if args_type[i]:
                    give = args_type[i]
                else:
                    give = args[i]
            elif "NEG" in i:
                give = ""
            else:
                give = ""
            # print(give)
            nl = nl + " " + give

        print("$$$$$$$ "+nl+" $$$$$$$")

        return nl

    def break_fact(self, data):
        print("***************")
        print(data)
        sym = None
        if "and" in data:
            lst = data.split("and")
            sym = "and"
        elif "or" in data:
            lst = data.split("or")
            sym = "or"
        else:
            return self.query(data)

        # if conjugate

        nl_list = []

        for i in lst:
            nl = self.query(i)
            nl_list.append(nl)

        print("*****************")
        print(nl_list)

        if sym == "and":
            output = " ^ ".join(nl_list)

        elif sym == "or":
            output = " v ".join(nl_list)
        else:
            output = False

        return output

    def break_predicate(self, data):
        if "∩" in data:
            sym = "∩"
            lst = data.split("∩")
        elif "∪" in data:
            sym = "∪"
            lst = data.split("∪")
        else:
            return self.predicate_query(data), data

        # if conjugate

        nl_list = []
        for i in lst:
            nl = self.predicate_query(i)
            nl_list.append(nl)

        if sym == "∪":
            output = " or ".join(nl_list)
            refine = " v ".join(lst)

        elif sym == "∩":
            output = " and ".join(nl_list)
            refine = " ^ ".join(lst)
        else:
            output = False
            refine = False

        print("============================= nl_list")
        print(nl_list)
        print("============================= nl_list")

        return output, refine

    def break_logic(self, data):
        data = data.replace(' ', '')
        # print(data)
        if "<=>" in data:
            sym = "<=>"
            lst = data.split("<=>")
        elif "=>" in data:
            sym = "=>"
            lst = data.split("=>")
        else:
            return False, False
        # print(lst)
        # if true

        nl_list = []
        l_list = []
        for i in lst:
            res = self.break_predicate(i)
            nl = res[0]
            ll = res[1]
            l_list.append(ll)
            nl_list.append(nl)
        print(nl_list)

        if False in nl_list:
            return False, False

        if sym == "<=>":
            output = nl_list[0] + " if and only if " + nl_list[1] + "."
            refine = " <=> ".join(l_list)

        elif sym == "=>":
            output = "If " + nl_list[0] + ", we will have, " + nl_list[1] + "."
            refine = " => ".join(l_list)

        else:
            output = False
            refine = False

        print(output)

        return output, refine


"""test = UserPredict(True)
# print(test.query("Tom accuses Bob."))
test.query("Tom does not accuse Bob of stealing the money.")



"""