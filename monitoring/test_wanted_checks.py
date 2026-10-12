import unittest
from unittest.mock import patch
import wanted_checks as w

class WantedTests(unittest.TestCase):
    def movie(self, **changes):
        return dict(id=1, monitored=True, hasFile=False, isAvailable=True,
                    digitalRelease='2020-01-01T00:00:00Z', **changes)

    def test_release_and_monitoring_gates(self):
        now=1800000000
        movie=self.movie()
        self.assertTrue(w.eligible('radarr', movie, now))
        for field, value in [('digitalRelease', None), ('digitalRelease', '2099-01-01'),
                             ('monitored', False), ('hasFile', True), ('isAvailable', False)]:
            self.assertFalse(w.eligible('radarr', dict(movie, **{field: value}), now))
        self.assertTrue(w.eligible('radarr', dict(movie, digitalRelease=None, physicalRelease='2020-01-01'), now))

    def test_episode_airdate_and_series_monitoring(self):
        episode=dict(id=2, monitored=True, hasFile=False, series={'monitored': True}, airDateUtc='2020-01-01T00:00:00Z')
        self.assertTrue(w.eligible('sonarr',episode,1800000000))
        for changes in [dict(series={'monitored':False}),dict(airDateUtc=None),dict(airDateUtc='2099-01-01')]:
            self.assertFalse(w.eligible('sonarr',dict(episode,**changes),1800000000))

    def test_clock_queue_recovery_and_outage(self):
        now=1800000000
        state,count,age=w.observe('radarr',[self.movie()],[],{},now)
        self.assertEqual((count,age),(0,0))
        for tick in range(300,36001,300):
            state,count,age=w.observe('radarr',[self.movie()],[],state,now+tick)
        self.assertEqual((count,age),(1,36000))
        self.assertEqual(w.observe('radarr',[self.movie()],[{'movieId':1}],state,now+36000)[0],{})
        self.assertEqual(w.observe('radarr',[],[],state,now+36000)[0],{})
        self.assertEqual(w.observe('radarr',[self.movie()],[],state,now+38000)[1:],(0,0))

    def test_pagination_never_silently_truncates(self):
        with patch.object(w,'request',side_effect=[{'records':[{'id':1}], 'totalRecords':2}, {'records':[{'id':2}], 'totalRecords':2}]):
            self.assertEqual(len(w.paged('','wanted/missing',{})),2)
        with patch.object(w,'request',return_value={'records':[], 'totalRecords':10001}):
            with self.assertRaises(AssertionError):w.paged('','queue',{})
