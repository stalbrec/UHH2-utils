from __future__ import print_function

import sys,os
import FWCore.PythonUtilities.LumiList as LumiList
from Utilities.General.cmssw_das_client import get_data
sys.path.append(os.environ["CMSSW_BASE"]+"/src/UHH2/scripts/crab")
from DasQuery import autocomplete_Datasets


def get_mc_lumi_list(inputDataset="/QCD_Pt_300to470_TuneCP5_13TeV_pythia8/RunIIFall17MiniAODv2-PU2017_12Apr2018_94X_mc2017_realistic*/MINIAODSIM"):
    '''
    inputDataset: can contain wildcards and will be autocompleted
    
    returns: a dict with an entry for each dataset user inputs with das string as key and LumiList as value (assumes MC samples with only one run "1")
    '''
    inputDatasets = autocomplete_Datasets([inputDataset])
    result={}
    for dataset in inputDatasets:
        print(dataset)
        json_dict = get_data(host = 'https://cmsweb.cern.ch',query="lumi file dataset="+dataset,idx=0,limit=0,threshold=300)
        lumi_list = LumiList.LumiList()
        try:
            n_files = len(json_dict['data'])
            for i,file_info in enumerate(json_dict['data']):
                if(i>n_files):
                    break
                lumi_list += LumiList.LumiList(runsAndLumis={'1':file_info['lumi'][0]['number']})
        except:
            print('Did not find lumis for %s'%dataset)
        result.update({dataset:lumi_list})    
    return result

def write_lumi_list(inputDataset="/QCD_Pt_1000to1400_TuneCP5_13TeV_pythia8/RunIIFall17MiniAODv2-PU2017_12Apr2018_94X_mc2017_realistic_v14*/MINIAODSIM",filename="test.json"):
    results=get_mc_lumi_list(inputDataset)

    if(results and len(results.keys())>2):
        raise BaseException("the given inputDataset DAS string corresponds to more than two samples. This is a bit unusual.")

    else:
        result_keys = results.keys()
        if("ext" in result_keys[0]):
            result_keys = list(reversed(result_keys))
        results[result_keys[0]].writeJSON(fileName=filename)
        if(len(result_keys)>1):
            #if there are two results assume its nominal+ext sample:
            results[result_keys[1]].writeJSON(fileName=filename.replace('.json','_ext.json'))
    
if __name__=="__main__":
    write_lumi_list()
