import unittest
from unittest.mock import patch
import version_checks as v

class VersionChecks(unittest.TestCase):
    def test_stable_and_rebuild_order(self):
        self.assertGreater(v.version('6.4.4.10685-ls320'),v.version('6.4.4.10685-ls319'))
        self.assertGreater(v.version('v2.10.0'),v.version('v2.9.0'))
        for tag in ('latest','develop','v2.3.0-rc1','nightly','arm64v8-2.3.0'):
            self.assertIsNone(v.version(tag))
    def test_future_tag_discovery_filters_channels(self):
        tags=['latest','4.0.20.3014-ls327','4.0.21.4000-ls328','5.0.0-develop','arm64v8-9.0.0-ls999']
        self.assertEqual(v.candidate(tags,lsio=True),'4.0.21.4000-ls328')
        self.assertEqual(v.candidate(['1.31.1-alpine','1.30.6-alpine','1.30.5-alpine'],nginx=True),'1.30.6-alpine')
        with self.assertRaises(ValueError): v.candidate(['latest','develop'],lsio=True)
    def test_kometa_stable_fallback_after_nightly_churn(self):
        responses = [({'results':[{'name':'nightly'}], 'next':None}, {}),
                     ({'tag_name':'v2.5.3','prerelease':False,'draft':False}, {}),
                     ({'results':[{'name':x} for x in ['amd64-v2.5.3-ls999','v2.5.3-ls124','v2.5.3-ls123','v2.5.30-ls200']], 'next':None}, {})]
        with patch.object(v,'fetch',side_effect=responses) as f:
            self.assertEqual(v.discover('linuxserver/kometa',lsio=True),'v2.5.3-ls124')
            self.assertIn('name=2.5.3',f.call_args.args[0])
        responses[1] = ({'tag_name':'v2.6.0-rc1','prerelease':True}, {})
        with patch.object(v,'fetch',side_effect=responses):
            with self.assertRaises(ValueError): v.discover('linuxserver/kometa',lsio=True)

    def test_notification_release_levels(self):
        base = dict(service='sonarr', installed_tag='4.0.20.3014-ls327',
                    installed_version='4.0.20.3014', status='update')
        for tag, expected in [('5.0.0-ls1', 'major'), ('4.1.0-ls1', 'minor'),
                              ('4.0.21.4000-ls328', 'patch'),
                              ('4.0.20.3014-ls328', 'rebuild'), ('3.9.0-ls1', 'none')]:
            with self.subTest(tag=tag):
                self.assertEqual(v.update_level(dict(base, available_tag=tag)), expected)
        mutable = dict(base, installed_tag='latest', status='mutable-tag-changed')
        self.assertEqual(v.update_level(dict(mutable, available_tag='4.1.0')), 'minor')
        self.assertEqual(v.update_level(dict(mutable, installed_version='unknown', available_tag='4.1.0')), 'unknown')
        self.assertEqual(v.update_level(dict(base, available_tag='5.0.0', lookup_error='TimeoutError')), 'none')
        self.assertEqual(v.update_level(dict(base, available_tag='5.0.0', status='current')), 'none')
        plex = dict(base, service='plex', installed_tag='n/a', installed_version='1.42.1.123-abc')
        self.assertEqual(v.update_level(dict(plex, available_tag='1.42.2.456-def')), 'patch')
        self.assertEqual(v.update_level(dict(plex, available_tag='1.43.0.456-def')), 'minor')

    def test_registry_platform_config_identity(self):
        responses=[({'manifests':[{'digest':'sha256:amd','platform':{'architecture':'amd64','os':'linux'}},{'digest':'sha256:arm','platform':{'architecture':'arm64','os':'linux'}}]}, {'Docker-Content-Digest':'sha256:index'}),({'config':{'digest':'sha256:config'}},{}),({'architecture':'amd64','os':'linux'}, {})]
        with patch.object(v,'fetch',side_effect=responses) as f:
            d=v.registry('lscr.io/linuxserver/sonarr','latest','amd64')
            self.assertEqual(d['available_config'],'sha256:config')
            self.assertEqual(d['available_digest'],'sha256:index')
            self.assertIn('sha256:amd',f.call_args_list[1].args[0])
        with patch.object(v,'fetch',return_value=({'manifests':[]},{})):
            with self.assertRaises(ValueError): v.registry('lscr.io/linuxserver/sonarr','latest','amd64')

if __name__=='__main__': unittest.main()
