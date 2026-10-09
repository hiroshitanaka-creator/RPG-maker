"""Linux専用exec。入れ子QAへ外側sessionを渡し、PIDを変えず実コマンドへ移る。"""
import os
import sys
os.environ['EQUIPMENT_QA059_SESSION']=str(os.getsid(0))
os.execvpe(sys.argv[1],sys.argv[1:],os.environ)
