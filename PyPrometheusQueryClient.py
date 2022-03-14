from unittest import result
import requests
from urllib.parse import urljoin
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import json
#import statsmodels.api as sm
#import statsmodels.formula.api as smf
from PyBlakemere.PyMemoize.MemoizationDecorator import memoize
from PyBlakemere.PyMemoize.CacheBackendDisk import DiskCacheBackend
from pathlib import Path



class PrometheusQueryClient:
    def __init__(self, url, cache_path=None, cache_encrypt_at_rest=False, cache_ttl=3600, ssl_verify=True, auto_get_server_metrics=True):
        self.url = url
        self.ssl_verify = ssl_verify
        self.metrics = None

        # Dynamically generate the _do_query_cache function, with or without caching. 
        if(cache_path and False):
            @memoize(DiskCacheBackend(cache_path, encrypt_at_rest=cache_encrypt_at_rest), maxttl=cache_ttl, is_class_method=True)
            def query_function(self, path, params):
                return self.__do_query_direct(self, path, params)
        else:
            def query_function(self, path, params):
                return self.__do_query_direct(self, path, params)
        setattr(self, '__query_function', query_function)

        if(auto_get_server_metrics):
            self._get_all_metrics()


    def __do_query_direct(self, path, params):
        resp = requests.get(urljoin(self.url, path), params=params, verify=self.ssl_verify)
        response = resp.json()
        if response['status'] != 'success':
            raise RuntimeError('{errorType}: {error}'.format_map(response))
        return response['data']

    def _do_query(self, path, params):
        results = self.__query_function(path, params)
        return results 

    def _get_all_metrics(self):
        resp = requests.get(self.url + '/api/v1/label/__name__/values', verify=self.ssl_verify)
        content = json.loads(resp.content.decode('UTF-8'))
        
        if content['status'] != 'success':
            raise RuntimeError('{errorType}: {error}'.format(resp.status_code))
        
        self.metrics = [ item for item in content.get('data', {}) ]
        
        return


    def get_metrics_starting_with(self, targets):
        results = []
        for item in self.metrics:
            if any(target in item for target in targets):
                results.append(item)
        return results


    @staticmethod
    def _datetime_to_str(t):
        return t.strftime('%Y-%m-%dT%H:%M:%SZ') if (isinstance(t, datetime)) else t


    def query_range(self, query, start, end, step, timeout=None):
        # Make sure our start and end times are as strings rather than 
        start = PrometheusQueryClient._datetime_to_str(start)
        end   = PrometheusQueryClient._datetime_to_str(end)

        # Build the params 
        params = {'query': query, 'start': start, 'end': end, 'step': step}
        if (timeout and not params.get('timeout', False)): # FIXME: This test doesn't work. Always does the update
           params.update({'timeout': timeout})

        # Run the query. 
        # TODO: Externalize the api string
        results = self._do_query('api/v1/query_range', params)
        
        return results


    def get_general(self, query, start=None, end=None, step=None):

        enddt = datetime.now()
        startdt = enddt - timedelta(hours = 1)

        if (not start):
            start = startdt.strftime('%Y-%m-%dT%H:%M:%SZ')
        else:
            startdt = datetime.strptime(start, '%Y-%m-%dT%H:%M:%SZ')

        if(not end):
            end = enddt.strftime('%Y-%m-%dT%H:%M:%SZ')
        else:
            enddt = datetime.strptime(end, '%Y-%m-%dT%H:%M:%SZ')

        if (not step):
             step = '{}s'.format( round((enddt.timestamp() - startdt.timestamp()) / 500) )

        # Correct step size that is so small it will cause an error
        if ( ((enddt.timestamp() - startdt.timestamp()) / 500) > 11000):
            step = '{}s'.format( np.floor((enddt.timestamp() - startdt.timestamp()) / 11000) )
            print('Warning: step size too small. Setting to {}s'.format(step))


        results = self.query_range(query, start, end, step)
        
        return results


    def get_without_deltas(self, query, start=None, end=None, step=None):
        results = self.get_general(query, start, end, step)
        
        data = { '{} - {}'.format(r['metric']['__name__'], r['metric']['instance']): 
                pd.Series((np.float64(v[1]) for v in r['values']), index=(pd.Timestamp(v[0], unit='s') for v in r['values']))
                for r in results['result']}

        df = pd.DataFrame(data)

        return (results, df)                   


    def get_with_deltas(self, query, start=None, end=None, step=None):
        
        (results, df) = self.get_without_deltas(query, start, end, step)
        
        for col in df.columns:
            tmp = [ ] 
            items = df[col].to_list()
            for (index, _) in enumerate(items):
                if (index == 0):
                    tmp.append(0)
                else:
                    tmp.append( items[index] - items[index - 1] )
            df['delta_{}'.format(col)] = tmp

        return (results, df)                   


    def get_metric(self, metric, start=None, end=None, step=None):
        
        if (not metric in self.metrics):
            raise ValueError("Metric '{}' is unknown".format(metric))
        
        is_cummulative = any(item in metric for item in ['_total'])
        if (is_cummulative):
            results = self.get_with_deltas(metric, start, end, step)
        else:
            results = self.get_without_deltas(metric, start, end, step)

        return results





if __name__ == '__main__':
    import urllib3
    urllib3.disable_warnings()

    api_url = "https://azlappjaegrs1.mfcgd.com/prometheus/"
    js = PrometheusQueryClient(api_url, cache_path='./.cache_tmp/', cache_ttl=3600)

    targets = [ 'node_network_carrier_changes_total', 'node_network_transmit_bytes_total' ]
    metrics = js.get_metrics_starting_with(targets)
    starttime = '2022-02-16T10:51:32Z'
    endtime   = '2022-02-17T10:59:22Z'


    results = {}
    for metric in metrics:
        print("Getting results for metric '{}'".format(metric))
        results[metric] = {}
        (results[metric]['data'], results[metric]['df']) = js.get_metric(metric, start=starttime, end=endtime)

    