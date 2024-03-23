import os
import sys
import yaml
import curses

from .defaults import CFG_PATH, CFG_FILENAME

## what about this in 'defaults.py' though?
## plus doesnt this pertain to the whole Viewer, project file paths etc?
##   we can import from defaults but then all these files are getting interdependent
#CFG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../cfg'))
#not os.path.isdir(CFG_PATH) and os.mkdir(CFG_PATH)
#DEFAULT_CFGFILE = os.path.join(CFG_PATH, "cfg.yml")
#CFG_FILENAME = os.path.join(
#    CFG_PATH,
#    os.path.splitext(os.path.split(sys.argv[0])[1])[0] + ".yml",
#    )


## CFG functions for classes that have:
##  cfg_filename,
##  CfgDict,
##  DEFAULT_CFG
## passes in 'cfgname' since some things are 'slot' some are 'device'

## should this be a 'classmethod'?
def CFGSAVE222(self, cfgname, cfgdict=None, no_trim=False):
    if no_trim:     
        _data = self.CfgDict
    else:
        _data = _cfg_dict_trim((cfgdict if cfgdict else self.CfgDict), self.DEFAULT_CFG)

    DATA = dict()
    if os.path.isfile(self.cfg_filename):
        with open(self.cfg_filename, 'r') as fp:
            DATA = yaml.full_load(fp)

        DATA.update({ cfgname : _data })

    #print("SAVE")
    #print(cfgname)
    #print(_data)
    #print(DATA)
    if _data:
        with open(self.cfg_filename, 'w') as fp:
            yaml.dump(DATA, fp)
        

def CFGLOAD222(self, cfgname):
    if os.path.isfile(self.cfg_filename):
        with open(self.cfg_filename, 'r') as fp:
            DATA = yaml.full_load(fp)

        _data = DATA.get(cfgname, None)

        #print("LOAD")
        #print(cfgname)
        #print(_data)
        #print(DATA)
        if _data:
            #for attr in self.DEFAULT_CFG.keys():
            for attr in _data.keys():
                _val = _data.get(attr, None)
                #print(attr)
                #print(_val)
                if _val != None:
                    setattr(self, attr, _val)
   

def _cfg_dict_trim(current, defaults):
    _data   = current
    _new    = dict()
    try:
        for k, v in _data.items():
            if k not in defaults or v == None:
                continue 

            #print(k, v)
            _v = defaults.get(k, None)
            if not isinstance(_v, type(None)) and v == _v:
                continue


            _new.update({ k : v })

    except Exception as ee:
        curses.endwin()
        print(_data)
        raise ee

    return _new

    ############################################################################
    ############################################################################

## Smaller and not using 'self'
##################################################
def CFGSAVE_LITE222(
    cfgname,
    cfgdict,
    cfgfilename,
    cfgdict_default=None,
    trim=True,
    ):

    #_data = _cfg_dict_trim(cfgdict, cfgdict_default) if trim else cfgdict
    _data = cfgdict
    if trim:
        _data = {}
        for k, v in cfgdict.items():
            if v == None or k not in cfgdict_default:
                continue

            _v = cfgdict_default.get(k, None)
            if v == _v and not isinstance(_v, type(None)):
                continue

            _data.update({ k : v })

    DATA = {}
    if os.path.isfile(cfgfilename):
        with open(cfgfilename, 'r') as fp:
            DATA = yaml.full_load(fp)

        DATA.update({ cfgname : _data })

    if _data:
        with open(cfgfilename, 'w') as fp:
            yaml.dump(DATA if DATA else _data, fp)
        

def CFGLOAD_LITE222(cfgname, cfgfilename):
    if os.path.isfile(cfgfilename):
        with open(cfgfilename, 'r') as fp:
            DATA = yaml.full_load(fp)

        if cfgname in DATA:
            return DATA[cfgname]

    return {}


   
