from pandas import read_excel, concat, merge, to_datetime
from numpy import nan

from pandas import Series, DataFrame


def record_creation(cutoff):
   
    ### Clean cases_raw
    def cases_csv_to_xlsx(cutoff: int):
        ## Load in data
        cases_raw = read_excel("./data/source/coded_all_cases_combined.xlsx")

        ## Seperate chronic and acute
        cases_raw['Classification'] = cases_raw['Disease'].str.split(', ').str[1]
        cases_raw['Classification'] = cases_raw['Classification'].replace('chron','chronic')

        ## Drop disease column and rows that are not before 2015
        last_decade = cases_raw[cases_raw['Year'] >= cutoff].copy().drop('Disease', axis= 1).reset_index(drop = True)

        ## Clean Antibody Test
        last_decade['total_anti_HCV_Date'] = last_decade['total_anti_HCV_Date'].dt.date

        ## Clean RNA Test
        last_decade['HCV_RNA_Date'] = last_decade['HCV_RNA_Date'].dt.date

        ## Clean Genotype Test
        last_decade['Specimen_Collection_Date__HCV_Ge'] = last_decade['Specimen_Collection_Date__HCV_Ge'].dt.date

        ## Organize Columns

        cases_clean = last_decade[['coded ID','Year','Classification','Investigation_Case_Status',
                                'Patient_State','County',
                                'total_anti_HCV_Date', 'total_anti_HCV',
                                'HCV_RNA_Date','HCV_RNA',
                                'Specimen_Collection_Date__HCV_Ge','HCV_Genotype']].copy()

        cases_clean.columns = ['patient_id','year','hep_c_classification', 'case_status',
                            'state','county',
                            'antibody_test_date','antibody_test_result',
                            'rna_test_date','rna_test_result',
                            'genotype_test_date','hcv_genotype']
        
        return cases_clean

    def labs_csv_to_xlsx(cutoff: int):
        ### Clean labs_raw
        labs_raw = read_excel("./data/source/coded_all_labs_combined.xlsx")

        ## Standardize Naming
        labs_lower = labs_raw.copy()
        labs_lower['Resulted_Test_Name'] = (
                labs_lower['Resulted_Test_Name']
                .str.lower()
                .str.replace('hepatitis c virus', 'hcv')
                .str.replace('hepatitis c', 'hcv')
                .str.replace('hep c', 'hcv')
            )

        ## Drop Tests without hcv
        good_tests = labs_lower[(labs_lower['Resulted_Test_Name'].str.contains('hcv',na=False))]
        good_tests_dated = good_tests[good_tests['Date_Specimen_Collected'].dt.year >= cutoff].copy().reset_index(drop = True)

        ## Broaden test names
        prefix_test = good_tests_dated['Resulted_Test_Name'].str.split(' ', expand=True).loc[:,1:2]

        def broaden_test(row):
            ab_test_name_mapper = ['ab','ab.','ab.igg','antibody','antigen','hcv','igg','rapid','total','virus']
            rna_test_name_mapper = ['or','qnt','qnt,logiu/ml','quant','quant,iu/ml','quantitative','rna','rna,','rna-pcr',]
            geno_test_name_mapper = ['(hcv)','genotype','gentyp','high-res','ns3','ns5','ns5a']

            if row[1] == '(hcv),':
                if ['eia','antibody,','antibody'].__contains__(row[2]):
                    test = 'antibody'
                elif row[2] == 'quantiative':
                    test = 'rna'
                else:
                    test = 'genotype'
            
            elif ab_test_name_mapper.__contains__(row[1]):
                test = 'antibody'
            elif rna_test_name_mapper.__contains__(row[1]):
                test = 'rna'
            elif geno_test_name_mapper.__contains__(row[1]):
                test = 'genotype'
            else:
                test = 'rna'
            
            return test
            
        good_tests_dated['broad_test_name'] = prefix_test.apply(broaden_test,axis = 1)

        cleaned_tests = good_tests_dated.copy()

        ## Combine all lab results
        cleaned_tests['lab_result'] = good_tests_dated['Coded_Result'].fillna(good_tests_dated['Numeric_Results']).fillna(good_tests_dated['Text_Result'])
        cleaned_tests['lab_result'] = cleaned_tests['lab_result'].str.lower()

        ## Seperate date information
        cleaned_tests['time_collected'] = cleaned_tests['Date_Specimen_Collected'].dt.time
        cleaned_tests['year'] = cleaned_tests['Date_Specimen_Collected'].dt.year
        cleaned_tests['date'] = cleaned_tests['Date_Specimen_Collected'].dt.date

        labs = cleaned_tests[['coded ID','Reporting_Facility',
                        'date','broad_test_name','lab_result']].copy()

        labs.columns = ['patient_id','facility',
                        'test_date','test_type','test_result']
        
        return labs

    ### Set up for wideform
    def clean_cases(cutoff: int):

        ## Reset classification
        cases_df = cases_csv_to_xlsx(cutoff)
        cases_df['classification'] = [x if x == 'chronic' else 'acute' for x in cases_df['hep_c_classification']]

        set_classification = cases_df.groupby('patient_id').agg({'classification':'unique','year':'unique','county':'first','state':'first'})
        set_classification['ordered_classification'] = ['chronic' if x == "['chronic']" else 'acute' if x == "['acute']" else 'acute -> chronic' for x in set_classification['classification'].astype(str)]

        ## Set aside patient info
        basic_patient_info = set_classification[['ordered_classification','state','county','year']].reset_index()
        basic_patient_info.columns = ['patient_id','classification','state','county','years_in_case']

        ## Splinter tests
        antibody_tests = (
            cases_df[['patient_id','antibody_test_date','antibody_test_result']]
            .copy()
            .sort_values(['patient_id','antibody_test_date','antibody_test_result']) ## So positive results are on top
        )
        antibody_tests['test_type'] = 'antibody'
        antibody_tests.columns = ['patient_id','test_date','test_result','test_type']

        rna_tests = (
            cases_df[['patient_id','rna_test_date','rna_test_result']]
            .copy()
            .sort_values(['patient_id','rna_test_date','rna_test_result'])
            .dropna(subset='rna_test_result') ## So positive results are on top
        )
        rna_tests['test_type'] = 'rna'
        rna_tests.columns = ['patient_id','test_date','test_result','test_type']

        geno_tests = (
            cases_df[['patient_id','genotype_test_date','hcv_genotype']]
            .copy()
            .sort_values(['patient_id','genotype_test_date','hcv_genotype'])
            .dropna(subset='hcv_genotype') ## So positive results are on top
        )
        geno_tests['test_type'] = 'genotype'
        geno_tests.columns = ['patient_id','test_date','test_result','test_type']

        all_case_tests = concat([antibody_tests,rna_tests,geno_tests]).sort_values('patient_id')
        all_case_tests['test_result'] = all_case_tests['test_result'].str.lower()

        return basic_patient_info,all_case_tests

    def clean_labs(cutoff):
        
        ### Now labs
        all_labs = labs_csv_to_xlsx(cutoff)

        all_labs_tests = all_labs.copy()

        ## Antibodies
        ab_labs = all_labs_tests[all_labs_tests['test_type'] == 'antibody'].copy() ## Don't reset index
  
        ab_labs['negative'] = ab_labs['test_result'].str.contains("|".join(['neg','non','equiv','nr']),na = False)
        ab_labs['positive'] = (
            (
                (ab_labs['test_result'].str.contains("|".join(['pos','react','present','detected']),na = False)) ## Basic
                | (ab_labs['test_result'].str.contains(r'[0-9]',na = False)) ## All numbers are positive
            ) & (ab_labs['negative'] == False)) ## Remove non-reactive
        ab_labs['indeterminate'] = ((ab_labs['negative'] == False) & (ab_labs['positive'] == False))

        ab_labs['test_result'] = nan
        for col in ['negative','positive','indeterminate']:
            ab_labs[col] = ab_labs[col].replace([True,False],[col,nan])
            ab_labs['test_result'] = ab_labs['test_result'].fillna(ab_labs[col])

        ab_results = ab_labs['test_result'].copy()

        ## RNA
        rna_labs = all_labs_tests[all_labs_tests['test_type'] == 'rna'].copy() ## Don't reset index

        rna_labs['tnp'] = rna_labs['test_result'].str.contains("|".join(['tnp','test not','credited','cancelled','insufficient sample']),na = False)
        rna_labs['no_result'] = rna_labs['test_result'].str.contains("|".join(['invalid','qns','pending']),na = True)
        rna_labs['indeterminate'] = rna_labs['test_result'].str.contains("|".join(['see','comment','not quantified','indeterminate']),na = False)
        rna_labs['negative'] = rna_labs['test_result'].str.contains("|".join(['undetect','not detect','non','negative','<','result value','below']),na = False)
        rna_labs['positive'] = rna_labs.iloc[:,rna_labs.columns.get_loc('tnp'):].apply(lambda x: x.sum(),axis = 1) == 0

        rna_labs['test_result'] = nan
        for col in ['tnp','no_result','indeterminate','negative','positive']:
            rna_labs[col] = rna_labs[col].replace([True,False],[col,nan])
            rna_labs['test_result'] = rna_labs['test_result'].fillna(rna_labs[col])

        rna_results =  rna_labs['test_result'].copy()

        ## Update with new values
        just_clean_labs = all_labs_tests.copy()
        just_clean_labs.loc[just_clean_labs['test_type'] == 'antibody','test_result'] = ab_results
        just_clean_labs.loc[just_clean_labs['test_type'] == 'rna','test_result'] = rna_results

        just_clean_labs = just_clean_labs.rename(columns = {'facility':'test_facility'})

        return just_clean_labs
    
    ## Get cases and labs
    class_loc, cases = clean_cases(cutoff)
    labs = clean_labs(cutoff)

    concat_tests = (
        concat([cases,labs])
        .sort_values(['patient_id','test_date', ## Primary
                      'test_type','test_result']) ## Clean out Nulls
        .drop_duplicates(['patient_id','test_date','test_type'])
        .reset_index(drop = True)
    )

    all_tests_long = merge(class_loc,concat_tests,how='right',on='patient_id')

    ## Sort columns
    all_tests_long = all_tests_long[['patient_id','classification',
                                     'state','county','years_in_case','test_facility',
                                     'test_date','test_type','test_result']]


    ## Make a copy for widening, droping info for the moment
    all_tests = all_tests_long.copy().drop(['classification','state','county','years_in_case'],axis = 1)

    ## Pivot for by patient
    all_tests['lab_number'] = all_tests.groupby('patient_id').cumcount() + 1
    all_tests_wide = all_tests.pivot(index='patient_id', columns=['lab_number'])

    ## Swap the levels so lab_number comes first
    all_tests_wide = all_tests_wide.reorder_levels(['lab_number',None], axis=1).sort_index(axis=1, level=[0, 1])

    # Sort by the new order
    all_tests_wide = all_tests_wide.sort_index(axis=1, level=[0, 1])

    ## Save lab data
    all_tests_long.to_csv('./data/output/hcv_labs_long.csv')
    all_tests_wide.reset_index().to_csv('./data/output/hcv_labs_wide.csv')

    return all_tests_wide,all_tests_long

def gen_patient_status(data):
    long = data.dropna(subset = 'test_date').copy().reset_index(drop=True)

    long['lab_number'] = long.groupby('patient_id').cumcount() + 1

    ## Handle patient lag
    lag_year = long['test_date'].max().year - 1

    if long['test_date'].max().day > 15:
        lag_month  = long['test_date'].max().month - 1
    else:
        lag_month  = long['test_date'].max().month - 2

    lag_date = to_datetime(f'{lag_year}-{lag_month}-01',yearfirst=True).date()

    ## Handle patient lag
    inclusion_list = long[((long['lab_number'] == 1) & (long['test_date'] < lag_date))].patient_id.drop_duplicates().reset_index(drop=True)
    step_1 = merge(long,inclusion_list,how='inner')

    cc_list = []

    for pat in step_1['patient_id'].drop_duplicates():

        ## Initialize each patient
        labs_list = step_1[step_1['patient_id'] == pat].reset_index(drop = True)
        stage = 0
        infection = 1 ## Start with first infection, infection >1 means reinfection
        for lab in labs_list.itertuples(index=True):

            ## Get stage information
            if (lab.test_type == 'antibody') & (lab.test_result == 'positive') & (stage == 0): ## Only time a positive antibody matters
                stage = 1
            elif (lab.test_type == 'rna') & (lab.test_result == 'negative'):
                if stage >= 3: ## Means they must have had a positive RNA
                    stage = 4
                else:
                    stage = 2
            elif (lab.test_type == 'rna') & (lab.test_result == 'positive'):
                if stage == 4: ## Must have been marked as cleared
                    infection += 1
                stage = 3
            elif (lab.test_type == 'genotype') & (Series(lab.test_result).astype(str).str.contains(r'\d',regex=True)[0]): ## all positive, only about 8% of genotype fail this test
                stage = 3
            
            ## Complile lab info
            lab_info = {
                'patient':lab.patient_id,
                'infection': infection,
                'year': lab.test_date.year,
                'lab_n': lab.lab_number,
                'stage': stage
            }

            cc_list.append(lab_info)

    cc_df = DataFrame(cc_list)

    ## Focusing on just the cc, we only need the most recent test each year(?)
    patient_status =(
        cc_df
        .copy()
        .dropna(subset='year')
        .drop_duplicates(['patient','infection','year'],keep='last')
        .drop('lab_n',axis = 1)
        .reset_index(drop = True)
    )

    ## Clean up variables
    patient_status['year']= patient_status['year'].astype(int)
    patient_status['status_float'] = patient_status['infection'] + (patient_status['stage']/10)
    patient_status_infected = patient_status[patient_status['status_float'] > 1.0].copy().reset_index(drop=True)


    county_list = step_1[['patient_id','county']].drop_duplicates().reset_index(drop=True).copy()

    ps_w_county = merge(patient_status_infected,county_list,left_on='patient',right_on='patient_id',how='left')

    patients_now = (
        ps_w_county
        .copy()
        .dropna(subset=['year'])
        .drop_duplicates('patient',keep='last')
        .reset_index(drop = True)
    )

    patient_status_infected.to_csv('./data/output/patient_status_table.csv',index=False)
    ps_w_county.to_csv('./data/output/patient_status_table_w_county.csv',index=False)
    patients_now.to_csv('./data/output/patients_status_now.csv',index=False)
    print('Patient status tables generated!')

    #### ================================================== Value Counts ==================================================
    patients_now['viral_testing'] = patients_now['status_float'] >= 1.2
    patients_now['initial_infection'] = patients_now['status_float'] >= 1.3
    patients_now['cured_or_cleared'] = patients_now['status_float'] >= 1.4
    patients_now['reinfection'] = patients_now['status_float'] > 1.4

    ## Gets base value counts
    val_counts = [{
        'Stage':'ever_infected',
        'Counted as Cases':len(patients_now.dropna(subset='county')),
        'Not Counted As Cases':patients_now['county'].isna().sum()
    }]

    for col in patients_now.iloc[:,7:].columns.to_list():
        val_counts.append({
            'Stage':col,
            'Counted as Cases':patients_now.dropna(subset='county')[col].sum(),
            'Not Counted As Cases':patients_now.loc[patients_now['county'].isna(),col].sum()
        })

    val_counts_df = DataFrame.from_dict(val_counts)

    val_counts_df.to_csv('./data/output/value_counts.csv')

    ## Now with county
    patients_now_agg = (
        patients_now
        .groupby('county')
        .agg(
            ever_infected = ('patient','nunique'),
            initial_infection = ('initial_infection','sum'),
            viral_testing = ('viral_testing','sum'),
            cured_or_cleared = ('cured_or_cleared','sum'),
            reinfection = ('reinfection','sum')
        )
    )
    patients_now_agg.T.to_csv('./data/output/value_counts_w_county.csv')
    
if __name__ == '__main__':
    CUTOFF = 2015

    print('Cleaning lab data...')
    wide, long  = record_creation(CUTOFF)
    print('Lab data has been cleaned!')

    print('Generating patient status information...')
    gen_patient_status(long)
    print('Value count tables generated!')

