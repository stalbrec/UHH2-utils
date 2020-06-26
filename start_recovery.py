from __future__ import print_function
import sys,glob,os
from search_spreadsheet import search_spreadsheet
import lumi_list_from_das

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--part','-p',type=int, default=1)
    args=parser.parse_args()
    
    print("starting recovery of lost ntuples...")
    workdir = 'tmp_workdir'
    if(not os.path.isdir(workdir)):
        os.makedirs(workdir)
    mask_dir = 'LumiMasks'
    if(not os.path.isdir(mask_dir)):
        os.makedirs(mask_dir)

    uhh2_dataset_dir = os.environ["CMSSW_BASE"]+"/src/UHH2/common/UHH2-datasets/"
    affected_dirs=[
        'RunII_102X_v2/2017/QCD/QCD_Pt_1000to1400_TuneCP5_13TeV_pythia8',
        'RunII_102X_v2/2017/QCD/QCD_Pt_1400to1800_TuneCP5_13TeV_pythia8',
        'RunII_102X_v2/2017/QCD/QCD_Pt_170to300_TuneCP5_13TeV_pythia8',
        'RunII_102X_v2/2017/QCD/QCD_Pt_1800to2400_TuneCP5_13TeV_pythia8',
        'RunII_102X_v2/2017/QCD/QCD_Pt_2400to3200_TuneCP5_13TeV_pythia8',
        'RunII_102X_v2/2017/QCD/QCD_Pt_300to470_TuneCP5_13TeV_pythia8',
        'RunII_102X_v2/2017/QCD/QCD_Pt_3200toInf_TuneCP5_13TeV_pythia8',
        'RunII_102X_v2/2017/QCD/QCD_Pt_470to600_TuneCP5_13TeV_pythia8',
        'RunII_102X_v2/2017/QCD/QCD_Pt_600to800_TuneCP5_13TeV_pythia8',
        # 'RunII_102X_v2/2017/QCD/QCD_Pt_800to1000_TuneCP5_13TeV_pythia8'
    ]
    
        
    for affected_dir in affected_dirs:
    
        affected_xmls=glob.glob(uhh2_dataset_dir+affected_dir+'*.xml')
        print(affected_xmls)
        info = search_spreadsheet("RunII_102X_v2","2017",affected_dir.split("/")[-1])
        info_skim = info[info["das"].str.contains(r"\*")] if len(info)>1 else info
        try:
            das_string = info_skim["das"].values[0]
        except:
            raise(Exception('Did not find any entry in spreadsheet!'))
        print(das_string)

        lumi_file_name = affected_dir.split('/')[-1]+'.json'
        if(not os.path.isfile(lumi_file_name)):
            lumi_list_from_das.write_lumi_list(inputDataset=das_string, filename=lumi_file_name)
        
        if(args.part==0):
            continue
        for unhealthy_xml in affected_xmls:
            #comment out bad xmls
            xml = unhealthy_xml.split('/')[-1]
            if(args.part==1):
                os.system('cp '+unhealthy_xml+' '+xml)
                print('./commentOutBadXML.sh '+xml+' missing_ntuples.list')
                os.system('./commentOutBadXML.sh '+xml+' missing_ntuples.list')
                #convert healthy xmls into plain text
                print('./xmlToTxt.sh '+xml.replace('.xml','_nobad.xml')+' '+xml.replace('.xml','_nobad.txt'))
                os.system('./xmlToTxt.sh '+xml.replace('.xml','_nobad.xml')+' '+xml.replace('.xml','_nobad.txt'))
                #dump lumilist from healthy ntuples
                print('./splitAndDumpLumiList.sh '+xml.replace('.xml','_nobad.txt')+' lumilist_'+xml.replace('.xml','_nobad.json'))
                os.system('./splitAndDumpLumiList.sh '+xml.replace('.xml','_nobad.txt')+' lumilist_'+xml.replace('.xml','_nobad.json'))
            elif(args.part==2):
                #merge completetd json
                print('mergeJSON.py lumilist_'+xml.replace('.xml','_nobad*.json') +' --output lumilist_'+xml.replace('.xml','_nobad.json'))
                os.system('mergeJSON.py lumilist_'+xml.replace('.xml','_nobad*.json') +' --output lumilist_'+xml.replace('.xml','_nobad.json'))
                #compare jsons
                json_from_das = lumi_file_name.replace('.json','_ext.json') if 'ext' in xml else lumi_file_name
                print('compareJSON.py --sub '+json_from_das+' lumilist_'+xml.replace('.xml','_nobad.json')+' missing_'+xml.replace('.xml','.json'))
                os.system('compareJSON.py --sub '+json_from_das+' lumilist_'+xml.replace('.xml','_nobad.json')+' missing_'+xml.replace('.xml','.json'))
                
                #cleanup
                os.system('mv *'+xml.replace('.xml','*')+' '+workdir)
                os.system('mv '+json_from_das+' '+workdir+'/lumilist_from_das.json')
                os.system('mv '+workdir+'/missing_'+xml.replace('.xml','.json')+' '+mask_dir)
            #create crab template using the "diff"ed json as lumi mask
