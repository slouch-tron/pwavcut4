import os
import yaml
import curses


## CFG functions for classes that have:
##  cfg_filename,
##  CfgDict,
##  DEFAULT_CFG
## passes in 'cfgname' since some things are 'slot' some are 'device'


def CFGSAVE(self, cfgname, cfgdict=None, no_trim=False):
    curses.endwin()
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
        

def CFGLOAD(self, cfgname):
    curses.endwin()
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

