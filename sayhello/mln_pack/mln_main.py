from pracmln import MLN, Database
from pracmln import query, learn
from pracmln.mlnlearn import EVIDENCE_PREDS
import time
from pracmln.utils import locs
import pickle


class InfResult:
    def __init__(self, event, prob):
        self.event = event
        self.prob = prob
        print(self.event, self.prob)


class InferenceMachine:
    def __init__(self, mln_path, db_path):
        self.db_path = db_path
        self.mln_path = mln_path
        self.result = None

    def engine(self, ask):
        try:
            self.result = self.inference(ask)
            print("$$$$$$$$$$$$$$$$$$$$$$")
            print(self.result)
            print("$$$$$$$$$$$$$$$$$$$$$$")

            mln_result_list = []
            for i in self.result.keys():
                prob_num = str((self.result[i]) * 100)[0:5]
                this_obj = InfResult(i, prob_num)
                mln_result_list.append(this_obj)
            print(mln_result_list)
            print("INFERENCE Finished!")
            return mln_result_list

        except:
            print("Some error occurs during inference process!")
            print("--will use the last successful result...")
            return []

    def inference(self, inference_query):
        mln = MLN(mlnfile=self.mln_path,
                  grammar='StandardGrammar')
        db = Database(mln, dbfile=self.db_path)
        for method in ['EnumerationAsk'
                       # 'MC-SAT',
                       # 'WCSPInference',
                       # 'GibbsSampler'
                       ]:
            print('=== INFERENCE TEST:', method, '===')
            result = query(queries=inference_query,
                           method=method,
                           mln=mln,
                           db=db,
                           verbose=True,
                           multicore=False).run()
            print(result)
        if result:
            return result
        else:
            return []

    def learning(self):
        mln = MLN(mlnfile=self.mln_path, grammar='StandardGrammar')
        db = Database(mln, dbfile=self.db_path)
        for method in ('BPLL', 'BPLL_CG', 'CLL'):
            print('=== LEARNING TEST:', method, '===')
            learn(method=method,
                  mln=mln,
                  db=db,
                  verbose=True,
                  multicore=False).run()


"""a = InferenceMachine("inference.mln", "inference.db")
b = a.inference('steal,lie')"""
