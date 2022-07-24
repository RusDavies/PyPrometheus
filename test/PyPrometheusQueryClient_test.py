import unittest
from PyPrometheusQueryClient import PrometheusQueryClient
from pathlib import Path
import urllib3
from datetime import datetime, timedelta
import json

urllib3.disable_warnings()

def delete_folder(pth:Path) -> None:
    if (pth.exists()):
        for sub in pth.iterdir():
            if (sub.is_dir()):
                delete_folder(sub)
            else:
                sub.unlink()
        pth.rmdir()
    return


class TestPyPrometheusQueryClient(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Get our test configuration 
        with open('./test/config_test_PyPrometheusQueryClient.json', 'r') as file:
            tmp = file.read()
            cls.test_config = json.loads(tmp)

        # Fixup file and path strings into Path objects
        for item in ['cache_path', 'metrics_config_file']:
            cls.test_config[item]  = Path(cls.test_config[item])

        # Get our metrics configuration 
        with open(cls.test_config['metrics_config_file'], 'r') as file:
            tmp = file.read()
            cls.metrics = json.loads(tmp)


        # Build the default instantiations options dictionary
        cls.default_opts = opts = {}
        for item in ['url', 'cache_path', 'cache_encrypt_at_rest', 'ssl_verify', 'cache_ttl', 'auto_get_server_metrics']:
            if (item in cls.test_config):
                cls.default_opts[item] = cls.test_config[item]
        
        # Set some other config items. We'll use the PrometheusQueryClient static method to conver to strings of 
        # the right format.  Note, the function of _datetime_to_str() has its own unit test. 
        end = datetime.now()
        start = end - timedelta(hours=1)
        cls.test_config['end']   = PrometheusQueryClient._datetime_to_str(end)
        cls.test_config['start'] = PrometheusQueryClient._datetime_to_str(start)

        # FIXME: Make sure the user-provided cache path is inside if our test path

        return    

    def setUp(self) -> None:
        delete_folder(self.test_config['cache_path'])
        return super().setUp()

    # =========================
    # Helpers

    def _instantiate_instance(self, opts=None):
        if(not opts):
            opts = self.default_opts
        iut = PrometheusQueryClient(**opts)
        return iut

    def _build_params(self, metric_pos=0):
        # Build the query params
        query = list(self.metrics.keys())[metric_pos]
        start = self.test_config['start']
        end   = self.test_config['end']
        step = 5
        params = {'query': query, 'start': start, 'end': end, 'step': step, 'timeout': 5}
        
        return params 

    # =========================
    # Tests 
    # 


    @unittest.skip
    def test_constructor(self):
        opts = self.default_opts
        opts['auto_get_server_metrics'] = False

        iut = self._instantiate_instance(opts)
        self.assertIsNotNone( iut )
        
        return

    @unittest.skip
    def test__datetime_to_str(self):
        t = datetime.strptime('Jun 1 2005  1:33PM', '%b %d %Y %I:%M%p')
        expected = '2005-06-01T13:33:00Z'
        actual = PrometheusQueryClient._datetime_to_str(t)
        self.assertEqual(expected, actual)

    @unittest.skip
    def test__get_all_metrics(self):
        #
        # Via direct call to _get_all_metrics()
        # 

        # Instantiate with the auto_get_server_metrics disabled
        opts = self.default_opts
        opts['auto_get_server_metrics'] = False
        iut = self._instantiate_instance(opts)

        # Check that we have not metrics set 
        self.assertTrue( hasattr(iut, 'metrics' ) )
        self.assertIsNone( iut.metrics )

        # Call _get_all_metrics()
        self.assertTrue( hasattr(iut, '_get_all_metrics' ) )
        iut._get_all_metrics()

        # Check that we now do have metrics set
        self.assertIsNotNone( iut.metrics )
        self.assertGreater( len(iut.metrics), 0)

        #
        # Via instantiation
        # 

        # Instantiate with the auto_get_server_metrics enabled
        opts['auto_get_server_metrics'] = True
        iut = self._instantiate_instance(opts)

        # Check that we now do have metrics set
        self.assertIsNotNone( iut.metrics )
        self.assertGreater( len(iut.metrics), 0)

        return

    def test__do_query(self):
        # Instantiate with the auto_get_server_metrics disabled
        opts = self.default_opts
        opts['auto_get_server_metrics'] = False
        iut = self._instantiate_instance(opts)

        # Build the query parameters
        params = self._build_params()

        # Run the query using _do_query()
        self.assertTrue( hasattr(iut, '_do_query'))
        results = iut._do_query('api/v1/query_range', params)

        # Check that we got something useful 
        self.assertIsNotNone(results)


    # <<< Working
    # ==========================
    # Not yet working >>>


    @unittest.skip
    def test_query_range(self):
        # Instantiate with the auto_get_server_metrics disabled
        opts = self.default_opts
        opts['auto_get_server_metrics'] = False
        iut = self._instantiate_instance(opts)

        # Build the query parameters
        params = self._build_params()

        # Run the query using query_range()
        results = iut.query_range(**params)

        # Check that we got something useful 
        self.assertIsNotNone(results)

    @unittest.skip
    def test_get_general(self):
        self.skipTest('Test not yet implemented')

    @unittest.skip
    def test_get_general(self):
        self.skipTest('Test not yet implemented')

    @unittest.skip
    def test_get_metric(self):
        self.skipTest('Test not yet implemented')

    @unittest.skip
    def test_get_metric_exception_metric_unknown(self):
        self.skipTest('Test not yet implemented')

    @unittest.skip
    def test_get_with_deltas(self):
        self.skipTest('Test not yet implemented')

    @unittest.skip
    def test_get_without_deltas(self):
        self.skipTest('Test not yet implemented')


if (__name__ == '__main__'):
    unittest.main()
    
