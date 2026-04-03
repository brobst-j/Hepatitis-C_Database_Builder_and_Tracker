from pandas import read_csv, merge
from pandas import Series, DataFrame

long = read_csv('./data/output/hcv_labs_long.csv',index_col=0)
long['lab_number'] = long.groupby('patient_id').cumcount() + 1

## Handle patient lag
inclusion_list = long[((long['lab_number'] == 1) & (long['test_date'] < '2024-07-01'))].patient_id.drop_duplicates().reset_index(drop=True)
follow_up_list = long[((long['lab_number'] == 1) & (long['test_date'] >= '2024-07-01'))].patient_id.drop_duplicates().reset_index(drop=True)

step_1 = merge(long,inclusion_list,how='inner')
step_1_cuts = merge(long,follow_up_list,how='inner')


## Mapper for the possible stages
stages_mapper = {0: 'Negative Antibody',
                 1: 'Positive Antibody',
                 2: 'Negative RNA',
                 3: 'Positive RNA',
                 4: 'Cleared'}

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

patient_status_infected.to_csv('./data/output/patient_status_table.csv')
ps_w_county.to_csv('./data/output/patient_status_table_w_county.csv')
patients_now.to_csv('./data/output/patients_status_now.csv')

patients_now = read_csv('./data/output/patients_status_now.csv')

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