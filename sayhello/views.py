# -*- coding: utf-8 -*-
from flask import flash, redirect, url_for, render_template
from sayhello import app, db
from sayhello.forms import HelloForm
from sayhello.models import Message
from sayhello.natural_language_processing import UserPredict
from sayhello.data_read_write import SingleFunction
from sayhello.mln_pack.mln_utils import write_mln_files
from sayhello.mln_pack.mln_main import InferenceMachine
import os


inf_res_url = os.path.dirname(app.root_path) + "/sayhello/mln_pack/result.pkl"
mln_path = os.path.dirname(app.root_path) + "/sayhello/mln_pack/inference.mln"
db_path = os.path.dirname(app.root_path) + "/sayhello/mln_pack/inference.db"
func_url = os.path.dirname(app.root_path) + "/sayhello/commonData/func.pkl"
nen_url = os.path.dirname(app.root_path) + "/sayhello/commonData/nen.cmdata"


utils = UserPredict(nen_url=nen_url, func_url=func_url, debug_mode=False)
inf_machine = InferenceMachine(db_path=db_path, mln_path=mln_path)
answer_feedback = []


@app.route('/', methods=['GET', 'POST'])
def index():
    global answer_feedback
    fact_form = HelloForm()
    change = False
    if fact_form.validate_on_submit():
        change = True
        body = fact_form.body_textarea.data
        c_type = fact_form.c_type.data
        nl_body = body

        # Handle if user input facts
        if c_type == "Facts":
            query_result = utils.query(body)
            print("*************************")
            print(query_result)
            print("*************************")

            if query_result:
                body = str(query_result)
            else:
                # seems like emotional
                flash('您的评论可能不是事实，因此将不被接受。')
                return redirect(url_for('index'))

        if c_type == "Predicates":
            query_result = utils.break_logic(body)
            print("*************************")
            print(query_result)
            print("*************************")
            if query_result[0]:
                nl_body = query_result[0]
            else:
                # seems like with errors!
                c_type = "Emotional"
            body = query_result[1]

        if c_type == "Emotional":
            pass

        if c_type == "SubmitFunction":
            query_result = utils.query(body, True)
            print("*************************")
            print('Submitted Function!', query_result)
            print("*************************")

            if query_result:
                flash('成功提交一条行为至行为库。')
            else:
                # seems like emotional
                flash('您提交的行为似乎不能被识别，将不被接受。')
            return redirect(url_for('index'))

        if c_type == "Query":
            print("DO QUERY Inference... ")
            refresh_inf(body)
            return redirect(url_for('index'))

        message = Message(body=body, c_type=c_type, nl_body=nl_body)
        db.session.add(message)
        db.session.commit()
        flash('成功发表一条评论。')
        return redirect(url_for('index'))

    messages = Message.query.order_by(Message.timestamp.desc()).all()
    facts = []
    predicates = []
    emotionals = []
    for i in messages:
        if i.c_type == "Facts":
            facts.append(i)
        elif i.c_type == "Predicates":
            predicates.append(i)
        elif i.c_type == "Emotional":
            emotionals.append(i)

    entity_dict = utils.commonDB.fetch()
    nen_per = ','.join(entity_dict['PER'])
    nen_loc = ','.join(entity_dict['LOC'])
    nen_org = ','.join(entity_dict['ORG'])

    funcs = utils.funcDB.fetch()
    complex_functions = []
    for i in funcs:
        this = SingleFunction(i)
        complex_functions.append(this)

    # Read MLN result

    # Extract functions in mln format
    functions_mln = []
    functions_query = []
    for i in funcs:
        try:
            if len(i['args']) == 1:
                functions_query.append(i['verb'])
            functions_mln.append(i['function_mln'])
        except:
            print("bug handled!")
    functions_query = ",".join(functions_query)

    print("===============")
    print(functions_query)
    print("===============")

    # Write MLN KB files
    try:
        write_mln_files(facts, predicates, functions_mln, nen_per, nen_org, nen_loc, db_path, mln_path)
        print("Finished WRITING!")
    except:
        print("Write MLN db and mln failed...")

    return render_template('index.html', fact_form=fact_form,
                           predicates=predicates, facts=facts, emotionals=emotionals, nen_per=nen_per,
                           nen_loc=nen_loc, nen_org=nen_org, functions=complex_functions, infresult=answer_feedback)


@app.route('/refresh', methods=["GET"])
def refresh():
    global answer_feedback
    db.drop_all()
    db.create_all()
    print("Deleted comments Database")

    # Clear Named entity
    # Clear caches:
    utils.commonDB.comments = {'PER': [], 'LOC': [], 'ORG': []}

    with open(nen_url, mode='w') as file:
        file.write("")

    print("Deleted named entity!")

    # Delete inference result
    with open(inf_res_url, mode='w') as file:
        file.write("")
    answer_feedback = []

    print("Inference Result deleted!")

    return redirect(url_for("index"))


@app.route('/clear_func', methods=["GET"])
def clear_func():
    # Clear Functions
    # Clear caches:
    utils.funcDB.comments = []
    with open(func_url, mode='w') as file:
        file.write("")
    return redirect(url_for("index"))


def refresh_inf(query_string):
    global answer_feedback

    answer_feedback = inf_machine.engine(query_string)

    if answer_feedback:
        for i in answer_feedback:
            try:
                print("###################")
                print(i.event)
                print("###################")
                nl_result = utils.predicate_query(i.event)
                print("RESULT COMPILED!", nl_result)
                i.event = nl_result
            except:
                pass

    print("%%%%")
    print("Refreshed inference result.")
    print("%%%%")

    if answer_feedback:
        flash('马尔可夫逻辑网络的推理结果已更新。')
    else:
        flash('马尔可夫逻辑网络的推理结果现在不可用，因为信息还不够，或者推理过程中发生了一些错误。 将显示上一次成功推断的结果。')
    return redirect(url_for("index"))

