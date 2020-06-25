#!/usr/bin/env python
from __future__ import print_function
import requests,re,os,shutil,csv,pandas

def search_spreadsheet(branch, year, query, delete_tmp=False, sample_type="", search_column="das"):
    '''' 
    branch: this decides which google-doc will be parsed.

    year: this can be any string containing one of the years 2016,2017,2018 (i.e. "2016v3" will work).
    Based on this this method will search in the respective sheets in the given google-doc.

    query: the method will search for this in the specifed column of the given google-doc/sheet.

    delete_tmp: by default tmp dir containing "cached" spreadsheets is kept. This determines if it should be removed after the query

    sample_type: can be data, sig, bkg or "" and will determine in which sheet the method will look for `query`. 

    search_colum: specify in which column the method should search for `query`
    '''
    spreadsheet_url = "https://docs.google.com/spreadsheets/d/{doc_id}/export?format=csv&id={doc_id}&gid={sheet_id}"

    doc_ids = {
        "RunII_102X_v2":"1wqwhKtALjZcejfTXgWE5dPE3bpEo0VQmq52SGE4oab4",
        "RunII_102X_v1":"19LSGDYDcXwhwowhub_-dIHpalkSmkYABOnRDSRnj38U"
    }
    sheet_ids = {
        "bkg":{
            "2016":"1477167626",
            "2017":"1396292818",
            "2018":"0"
        },
        "sig":{
            "2016":"822571647",
            "2017":"571605227",
            "2018":"1537748452"
        },
        "data":{
            "2016":"2053028482",
            "2017":"637267164",
            "2018":"712721274"
        }
    }
    new_column_names = {
        'Sample Name':'das',
        'Lumi [pb^-1]':'lumi',
        'Short name':'name',
        'Cross-section [pb]':'xsec',
	'Number of events':'nevents',
	'Expected N events':'nexpected',
	'Comments':'comment',
        'x-sec checked':'checkedxsec',
        'Interested':'interested',
        'Person':'person'
    }

    
    year_match = re.search(r'201[678][A-Z]*', year)
    year = "2017" if not year_match else year_match.group()
    sample_info=[]
    sample_types = ['bkg','sig','data'] if sample_type=="" else [sample_type]
    for sample_type in sample_types:
        csv_filename = "tmp/"+branch+'_'+year+'_'+sample_type+'.csv'
        print('searching for',query,sample_type,'spreadsheet')
        if(not os.path.isfile(csv_filename)):
            if(not os.path.isdir("tmp")):
                os.makedirs("tmp")
            url = spreadsheet_url.format(doc_id=doc_ids[branch],sheet_id=sheet_ids[sample_type][year])
            print('downloading spreadsheet:',url)
            r = requests.get(url=url)
            open(csv_filename, 'wb').write(r.content)

        sample_info = pandas.read_csv(csv_filename)
        sample_info.dropna(subset=["Sample Name"],inplace=True)

        for column in new_column_names.keys():
            if(column not in sample_info.columns):
                sample_info[column]=None
        
        sample_info.rename(columns=new_column_names,inplace=True)
        
        if(sample_info[search_column].str.contains(query).any()):
            break         
    
    if(delete_tmp):
        shutil.rmtree("tmp")
        
    return sample_info[sample_info[search_column].str.contains(query)]

if(__name__=='__main__'):
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--deleteTmp',    action='store_true',                               help='remove "cached" version of spreadsheets.')
    parser.add_argument('-q','--query',   default='',                                        help='specify term to search for in spreadsheet column.', required=True)
    parser.add_argument('-c','--column',  default='das',                                     help='specify name of column that should be searched for specified query term.')
    parser.add_argument('-b','--branch',  default='RunII_102X_v2',                           help='specify which spreadsheet should be searched.')
    parser.add_argument('-t','--type',    default='',                                        help='specify what type of sample to look for.')
    parser.add_argument('-y','--year',    default='2017',                                    help='specify which year the results should correspond to.', type=str,choices=['2016', '2017', '2018'])
    parser.add_argument('--print_columns',default=['das','name','xsec','lumi','nevents'],    help='specify which columns should be printed.', nargs='+'   )
    parser.add_argument('-f','--filter',  default='', type=str,                              help='add one extra filter to the printed dataframe. For now accepts <,>,=,!=,=!,not,is and contains as comparing operators')
    args = parser.parse_args()

    if(args.deleteTmp):
        shutil.rmtree("tmp")
    
    query = search_spreadsheet(args.branch, args.year, args.query, delete_tmp=False, sample_type=args.type, search_column=args.column)
    
    if(len(args.filter)>0):
        try:
            operator_str = re.search(r'(=!|!=|[<>=]|not|is|contains)',args.filter).group()
        except:
            # if viable operator is not found in filter string just fall back to "DAS IST NOT NONE!!! (which is always true, see above)"
            operator_str="not"
            args.filter="das not None"
        import operator
        def contains_(series,query):
            return series.str.contains(query)
        operator_ = {'<':operator.__lt__,'>':operator.__gt__,'=':operator.__eq__,'is':operator.__eq__,'not':operator.__ne__,'!=':operator.__ne__,'=!':operator.__ne__,'contains':contains_}[operator_str]
        column = args.filter.split(operator_str)[0].strip()
        value = args.filter.split(operator_str)[1].strip().decode('utf-8')
        if(value.isdecimal()):
            value = float(value)
        if(operator_str=='contains'):
            query.dropna(subset=[column],inplace=True)
        print(query[args.print_columns][operator_(query[column],value)])

    else:
        print(query[args.print_columns])        
