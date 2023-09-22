import base64
from io import BytesIO

import pandas
import os
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from pandas.core.dtypes.common import is_categorical_dtype

from jinja2 import Environment, FileSystemLoader
from cleverminer import cleverminer

from cleverminer import cleverminer
import scipy.stats as ss

class pandas_cat:
    """
    Pandas categorical profiling. Creates html report with profile of categorical dataset. Provides also other useful functions.
    """

    version_string = "0.1.1"
    template_name = "default_0_1_0.tem"

    def __init__(self):
        """
        Initializes a class.

        """
    @staticmethod
    def profile(df:pandas.DataFrame=None,dataset_name:str=None,template:str=None,opts:dict=None):
        """
        Profiles a categorical dataset.

        :param df: pandas dataframe to profile
        :param dataset_name: dataset name
        :param template: 'default' or 'interactive' template for the final report
        :param opts: options

        Options inlude:
            * **auto_prepare** - set whether to apply automatic dataframe preparation (default = False)
            * **cat_limit** - limit number of categories to profile (default=20)
            * **missing_values** - array of additional custom values that should be detected as missing

        """
        self = pandas_cat

        # GENERATE INTERACTIVE REPORT
        if template == 'interactive':
            # Use default options if they were not specified by user
            default_options = {'auto_prepare': True, 'cat_limit': 20, 'missing_values': None}
            options = default_options if opts is None else {**default_options, **opts}

            # Prepare dataset if auto_prepare is on
            if options['auto_prepare'] is True:
                print('Progress 1/6: Preparing data...')
                df = self.handle_missing_values(df, options['missing_values'])
                df = self.prepare(df)

            print('Progress 2/6: Preparing attribute profiles...')

            # Storage for attribute profiles
            attribute_profiles = []

            # Iterate over each column in df
            for column in df.columns:
                # Count categories
                categories_counts = df[column].value_counts()
                # If categories count is over the limit remove attribute
                if len(categories_counts) > options['cat_limit']:
                    df.drop(column, axis=1, inplace=True)
                    continue
                # Count missing values
                missing_count = df[column].isnull().sum()
                # Get RAM usage
                formated_ram = self._humanbytes(
                    df.memory_usage(deep=True)[column])
                # Create profile for the attribute
                profile = {
                    'attribute': column,
                    'categories': categories_counts.index.tolist(),
                    'counts': categories_counts.values.tolist(),
                    'percentages': [round((val / (categories_counts.values.sum() + missing_count)) * 100, 2) for val in categories_counts.values.tolist()],
                    'missing': missing_count,
                    'ram': formated_ram
                }
                # Store profile
                attribute_profiles.append(profile)

            print('Progress 3/6: Calculating overall correlations...')

            # Storage for correlations
            correlations_data = {}
            correlations_data['Overall Correlations'] = []

            for column_one in df.columns:
                for column_two in df.columns:
                    confusion_matrix = pd.crosstab(df[column_one], df[column_two])
                    correlation = round(self._cramers_corrected_stat(confusion_matrix), 3)
                    entry = {"x": column_one,
                            "y": column_two, "v": correlation}
                    correlations_data['Overall Correlations'].append(entry)

            print('Progress 4/6: Calculating individual correlations...')

            # Iterate over each combination of columns
            for i, column_one in enumerate(df.columns):
                for j, column_two in enumerate(df.columns):
                    confusion_matrix = pd.crosstab(
                        df[column_one], df[column_two])
                    crosstab_data = confusion_matrix.to_dict(orient='split')
                    # Iterate over each combination of categories
                    for k, category_one in enumerate(crosstab_data['index']):
                        for l, category_two in enumerate(crosstab_data['columns']):
                            correlation = crosstab_data['data'][k][l]
                            entry = {"x": category_one,
                                    "y": category_two, "v": correlation}
                            key = f"{column_one} x {column_two}"
                            if key not in correlations_data:
                                correlations_data[key] = []
                            correlations_data[key].append(entry)

            print('Progress 5/6: Preparing html report...')

            # Load Jinja2 template
            env = Environment(loader=FileSystemLoader(f"{os.path.dirname(__file__)}/templates/interactive"))
            template = env.get_template('interactive.html')

            # Ready input data for the template
            data = {
                'title': dataset_name or 'DataFrame',
                'attribute_profiles': attribute_profiles,
                'correlations_data': correlations_data,
                'attribute_count': df.shape[1],
                'records_count': df.shape[0],
                'missing_count': df.isnull().sum().sum(),
                'total_ram': self._humanbytes(df.memory_usage(deep=True).sum())
            }

            # Render html using the template
            html = template.render(**data)

            # Write result in the file
            report_dir = os.path.join(os.getcwd(), 'report')
            if not os.path.exists(report_dir):
                os.makedirs(report_dir)
            filename = os.path.join(report_dir, f'{dataset_name.lower()}.html')
            with open(filename, 'w') as f:
                f.write(html)

            print(f'Progress 6/6: Report {dataset_name.lower()}.html finished...')
            return

        # GENERATE DEFAULT REPORT
        my_df = df
        if not(type(df) == pandas.core.frame.DataFrame):
            print("Cannot profile. Parameter df is not a pandas dataframe.")
            return
        if opts is not None:
            if "auto_prepare" in opts:
                if opts.get("auto_prepare") == True or opts.get("auto_prepare") == 1:
                    print("Will auto prepare data...")
                    my_df = self.handle_missing_values(df, opts['missing_values'])
                    my_df = self.prepare(df=my_df,opts=opts)
                    print("... auto prepare data done.")
        df = my_df

        warning_info = []

        #check limit on number of categories for each variable

        limit = 20

        if opts is not None:
            if "cat_limit" in opts:
                limit = opts.get("cat_limit")
        print(f"Will limit to {limit} categories.")

        to_drop=[]

        for var in df.columns:
            dff = df[var]
            lst = dff.unique()
            cnt=len(lst)
            print(f"...variable {var} has {cnt} categories")
            if cnt>limit:
                print(f"WARNING: variable {var} has been removed from profiling because it has {cnt} categories, which is over limit {limit}. Note you may increase the limit of allowed categories by setting the parameter cat_limit.")
                warning_info.append({'type':'alert-warning','text':'WARNING: variable '+var+' has been removed from profiling because it has '+str(cnt)+' categories, which is over the limit of '+str(limit)+' categories.<br> Note you may increase the limit of allowed categories by setting the parameter <i>cat_limit</i>.'})
                to_drop.append(var)
            if cnt==1 and lst[0]!=lst[0]:
                print(f"WARNING: variable {var} has been removed from profiling because it has only empty value.")
                warning_info.append({'type':'alert-warning','text':'WARNING: variable '+var+' has been removed from profiling because it has only empty value.'})
                to_drop.append(var)
            if cnt==0:
                print(f"WARNING: variable {var} has been removed from profiling because it has {cnt} categories")
                warning_info.append({'type':'alert-warning','text':'WARNING: variable '+var+' has been removed from profiling because it has '+str(cnt)+' categories.'})
                to_drop.append(var)
            if isinstance(var,list) or isinstance(var,tuple):# or isinstance(var,dict):
                print(f"WARNING: variable {var} has been removed from profiling because it has unsupported type ({type(var)})")
                warning_info.append({'type':'alert-warning','text':'WARNING: variable '+var+' has been removed from profiling because it has unsupported type ('+type(var)+').'})
                to_drop.append(var)

        if len(to_drop)>0:
            print(f"...will drop {to_drop}")
            df = df.drop(columns=to_drop)

        env = Environment(loader=FileSystemLoader(os.path.dirname(__file__)+'/'+'templates'))
        html_inner =""
        indi_variables =[]


        cntordr = 0

        print("Preparing summary...")
        size = df.memory_usage(deep=True).sum()
        size_str = str(f'{self._humanbytes(size)}')

        df_summary = {}
        df_summary['overall_table'] = {'Records': str(f'{len(df):,}'), 'Columns': str(f'{len(df.columns):,}'), 'Memory usage': size_str}

        varlist = df.columns

        summ_vars = []

        tmp_colname_for_chart = []
        tmp_name_for_chart = []
        tmp_val_for_chart = []
        lst_for_df = []

        for var in varlist:
            dff = df[var]
            var_size = dff.memory_usage(deep=True)
            var_size_str = str(f'{self._humanbytes(var_size)}')
            dfg = df.groupby(var)
            cat_list = ""
            cat_cnt = 0
            for grp_name, grp_rows in dfg:
                if cat_cnt>0:
                    cat_list = cat_list + ", "
                cat_list = cat_list + str(grp_name)
                cat_cnt += 1
            var_item = {'Attribute': var, 'Categories': cat_cnt, 'Categories_list': cat_list, 'Memory_usage': var_size,
                        'Memory_usage_hr': var_size_str}
            summ_vars.append(var_item)
            tmp_name_for_chart.append(var)
            tmp_colname_for_chart.append('Memory usage')
            tmp_val_for_chart.append(var_size)
            lst_for_df_sub = []
            lst_for_df_sub.append(var)
            lst_for_df_sub.append(var_size)
            lst_for_df.append(lst_for_df_sub)

        df_summary['Profiles'] = summ_vars


        #in following code we will not use _humanbytes as we need same unit for all items
        unit = "Bytes"
        tot_size = sum(tmp_val_for_chart)
        min_splitter = 3
        if tot_size > min_splitter * 1000000000000:
            unit = "TB"
            tmp_val_for_chart = [x / 1000000000000 for x in tmp_val_for_chart]
        elif tot_size > min_splitter * 1000000000:
            unit = "GB"
            tmp_val_for_chart = [x / 1000000000 for x in tmp_val_for_chart]
        elif tot_size > min_splitter * 1000000:
            unit = "MB"
            tmp_val_for_chart = [x / 1000000 for x in tmp_val_for_chart]
        elif tot_size > min_splitter * 1000:
            unit = "KB"
            tmp_val_for_chart = [x / 1000 for x in tmp_val_for_chart]

        tmp_name_for_chart.insert(0, "Memory usage")
        tmp_val_for_chart.insert(0, "")

        tmp_val_for_chart2 = []
        tmp_val_for_chart2.append(tmp_val_for_chart)

        tmp_df2 = pd.DataFrame(tmp_val_for_chart2, columns=tmp_name_for_chart)

        tmp_df2.plot(x='Memory usage', kind='bar', stacked=True, title='Memory usage by attribute')

        # reordering the labels
        handles, labels = plt.gca().get_legend_handles_labels()

        # specify order
        order = list(range(len(varlist)))
        order.reverse()

        # set legend and labels

        plt.legend([handles[i] for i in order], [labels[i] for i in order], bbox_to_anchor=(1, 1), loc=2, borderaxespad=0.)
        plt.tight_layout()
        plt.ylabel('Size in ' + unit)

        # save to stream

        tmpfile = BytesIO()
        plt.savefig(tmpfile, format='svg')
        encoded = base64.b64encode(tmpfile.getvalue()).decode('utf-8')
        df_summary['mem_usg_svg'] =  encoded

        print("Preparing summary...done")
        print("Preparing individual profiles...")


        for i in df.columns:
            df2 = df[[i]]
            cntordr += 1
            for j in df2.columns:
                fcont = self._plot_histogram(df2, j, sort=False, save=False, rotate=False)
                df3 = df2.groupby(j)

                is_ordered = False

                if is_categorical_dtype(df[i]):
                    if df[i].cat.ordered:
                        is_ordered = True

                most_frequent = None
                for grp_name, grp_rows in df3:
                    if most_frequent is None or most_frequent < len(grp_rows):
                        most_frequent = len(grp_rows)

                freq_tbl = []

                for grp_name, grp_rows in df3:
                    pct = len(grp_rows) / len(df2) * 100
                    fmt_width = len(grp_rows) / most_frequent * 100
                    pct_str = str(f'%.2f%%' % pct)
                    fmt_width_str = str(f'%.2f%%' % fmt_width)

                    freq_tbl_item = {'name': grp_name, 'count': len(grp_rows), 'pct': pct_str, 'pct_num': pct,
                                     'fmt_width': fmt_width_str}
                    freq_tbl.append(freq_tbl_item)

                fn = j + ".svg"
                summary = ""
                summary_tbl = {}
                summary += "Categories : " + str(len(df2[j].unique())) + "<br>"
                summary_tbl['Categories'] = str(len(df2[j].unique()))
                idxmax = df[j].value_counts().idxmax()
                idxmin = df[j].value_counts().idxmin()
                cnt_max = len(df2[df2[j] == idxmax])
                pct_max = cnt_max / len(df2) * 100
                cnt_min = len(df2[df2[j] == idxmin])
                pct_min = cnt_min / len(df2) * 100
                summary += "Most frequent : " + str(idxmax) + " (" + str(f'{cnt_max:,}') + " values, " + str(
                    f'%.2f%%' % pct_max) + ")<br>"
                summary_tbl['Most frequent'] = str(idxmax) + " (" + str(f'{cnt_max:,}') + " values, " + str(
                    f'%.2f%%' % pct_max) + ")"
                summary += "Least frequent : " + str(idxmin) + " (" + str(f'{cnt_min:,}') + " values, " + str(
                    f'%.2f%%' % pct_min) + ")<br>"
                summary_tbl['Least frequent'] = str(idxmin) + " (" + str(f'{cnt_min:,}') + " values, " + str(
                    f'%.2f%%' % pct_min) + ")"
                size = df2.memory_usage(deep=True).sum()
                size_str = str(f'{self._humanbytes(size)}')
                summary_tbl['mem_usage'] = size_str
                missings = df2[j].isna().sum()
                missings_pct = missings / len(df2) * 100
                summary += "Missings: " + str(f'{missings:,}') + " (" + str(f'%.2f%%' % missings_pct) + ")<br>"
                summary_tbl['Missings'] = str(f'{missings:,}') + " (" + str(f'%.2f%%' % missings_pct) + ")"
                d = {'varname': j, 'is_ordered': is_ordered, 'freq_table': None, 'freq_chart': None, 'fname': fn, 'fcont':fcont,
                     'cnt': cntordr, 'summary': summary, 'summary_tbl': summary_tbl, 'freq_tbl': freq_tbl}
                indi_variables.append(d)

        print("Preparing individual profiles...done")
        print("Preparing overall correlations...")

        #https://stackoverflow.com/questions/20892799/using-pandas-calculate-cram%C3%A9rs-coefficient-matrix
        dict_cramer = {'col1':[],'col2':[],'cnt':[]}
        df_cramer = pd.DataFrame(dict_cramer)

        for i in df.columns:
            for j in df.columns:
                confusion_matrix = pd.crosstab(df[i], df[j])
                cr= self._cramers_corrected_stat(confusion_matrix=confusion_matrix)
                df2= pd.DataFrame({'col1':[i],'col2':[j],'cnt':[cr]})
                #df_cramer.append(df2,ignore_index=True)
                df_cramer = pd.concat([df_cramer,df2],axis=0,ignore_index=True)
        ct=pd.crosstab(df_cramer['col1'],df_cramer['col2'],values=df_cramer['cnt'],aggfunc='mean')
        plt.figure(figsize=(16, 4))
        sns.heatmap(ct, annot=True, cmap='Blues', fmt='.2f',linewidth=1)
        tmpfile_c_o = BytesIO()
        plt.savefig(tmpfile_c_o, format='svg')
        plt.close()
        encoded_c_o = base64.b64encode(tmpfile_c_o.getvalue()).decode('utf-8')
        overall_corr = encoded_c_o

        print("Preparing overall correlations...done")
        print("Preparing individual correlations...")
        indiv_corr = {}

        for i in df.columns:
            print(f"... for variable {i}...")
            dict={'varname':i}
            dict2 = {}
            for j in df.columns:
                ct = pd.crosstab(df[i], df[j])
                print(f"...... doing crosstab {i} x {j}")
                plt.figure(figsize=(16, 4))
                sns.heatmap(ct,annot=True,cmap='Blues', fmt='g')
                tmpfile_c_i = BytesIO()
                plt.savefig(tmpfile_c_i, format='svg')
                plt.close()
                encoded_c_i = base64.b64encode(tmpfile_c_i.getvalue()).decode('utf-8')
                dict2[j]= encoded_c_i

            dict['vars'] = dict2
            indiv_corr[i] = dict

        corr = {}
        corr['overall_corr'] = overall_corr
        corr['indiv_corr'] = indiv_corr

        print("Preparing individual correlations...done.")
        print("Preparing output file...")


        fname = "report.html"

        outdir = os.path.join(os.getcwd(), 'report')
        # Check whether the specified path exists or not
        isExist = os.path.exists(outdir)
        if not isExist:
            # Create a new directory because it does not exist
            os.makedirs(outdir)
            print("The new directory is created!")
        outname = os.path.join(os.getcwd(), 'report', fname)

        # Load the template from the Environment

        template = env.get_template(self.template_name)

        dn=dataset_name

        if dn is None:
            dn = '&lt;pandas dataframe&gt;'

        html = template.render(dataset_name=dn,
                               warning_info=warning_info,
                               df_summary=df_summary,
                               indi_variables=indi_variables,
                               corr=corr,
                               version_string=pandas_cat.version_string
                               )

        with open(outname, 'w') as f:
            f.write(html)
        print("Preparing output file ...done")
        print("Finished preparing profile report.")
        print(f"Your report is ready in file {outname}")


    def _cramers_corrected_stat(confusion_matrix):
        """ calculate Cramers V statistic for categorial-categorial association.
            uses correction from Bergsma and Wicher,
            Journal of the Korean Statistical Society 42 (2013): 323-328
        """
        chi2 = ss.chi2_contingency(confusion_matrix)[0]
        n = confusion_matrix.sum().sum()
        phi2 = chi2 / n
        r, k = confusion_matrix.shape
        phi2corr = max(0, phi2 - ((k - 1) * (r - 1)) / (n - 1))
        rcorr = r - ((r - 1) ** 2) / (n - 1)
        kcorr = k - ((k - 1) ** 2) / (n - 1)
        return np.sqrt(phi2corr / min((kcorr - 1), (rcorr - 1)))

    def _plot_histogram(df, column,sort=False,save=False,save_folder=None,rotate=True):
        label_format = '{:,.0f}'
        data=df
        if sort:
            data=data.sort_values(by=column)
        grp=data.groupby(column, dropna=False)[column].count()

        plt.figure(figsize=(16, 4))
        a  = sns.barplot(x=grp.index, y=grp.values, color="lightsteelblue",edgecolor="black")
        if rotate:
            plt.xticks(rotation=90)

        ticks_loc = a.get_yticks().tolist()
        a.yaxis.set_major_locator(mticker.FixedLocator(ticks_loc))
        a.set_yticklabels([label_format.format(x) for x in ticks_loc])
        plt.tight_layout()
        if save:
            filename = ""
            if save_folder is not None:
                filename= save_folder+'\\'
            filename=filename+column+'.svg'
            plt.savefig(filename)
        else:
            tmpfile = BytesIO()
            plt.savefig(tmpfile, format='svg')
            encoded = base64.b64encode(tmpfile.getvalue()).decode('utf-8')
            fcont = encoded
            return fcont

    def _humanbytes(B):
        """Return the given bytes as a human friendly KB, MB, GB, or TB string."""
        power = 2**10
        n = 0
        power_labels = {0: 'B', 1: 'KB', 2: 'MB', 3: 'GB', 4: 'TB'}

        while B > power:
            B /= power
            n += 1

        return f"{B:.2f} {power_labels[n]}"

    @staticmethod
    def prepare(df:pandas.DataFrame=None,opts:dict=None):
        """
        Prepares a categorical dataset. Takes strings, integers etc. variables and if possible, converts it do
        pandas categorical and ordered by their natural value

        :param df: pandas dataframe to prepare (advance) in pandas categorical


        """
        #currently we are using CleverMiner's data preparation
        #we plan to create this package independent on CleverMiner package and move these routines from CleverMiner to this package


        my_df=df
        opts2=opts
        if opts2 is None:
            opts2 = {}
        opts2['keep_df'] = True
        clm = cleverminer(df=my_df, opts=opts2)
        if cleverminer.version_string < '1.0.7':
            return my_df
        return clm.df

    @staticmethod
    def handle_missing_values(df, values:list=None):
        """
        Replaces missing string values with real missing values.

        :param df: pandas dataframe
        :param values: array of additional custom values that should be also detected as missing values

        """
        default_missing_values = ['na', 'n/a', 'nan', 'null', 'none', 'missing', 'undefined']
        missing_values = default_missing_values if values is None else list(set(default_missing_values + values))

        for column in df.columns:
            df[column] = df[column].apply(lambda x: np.nan if str(x).lower() in missing_values else x)

        return df