from astra.providers import ProviderRegistry, ProviderResult
class Blocked:
    name='blocked'
    def fetch(self,*a,**k): return ProviderResult(self.name,'BLOCKED','network unavailable')
class Good:
    name='good'
    def fetch(self,*a,**k): return ProviderResult(self.name,'PROVIDER_VERIFIED','fixture-backed provider result')
def test_registry_fails_over_after_blocked_provider():
    rs=ProviderRegistry([Blocked(),Good()]).fetch_first_verified('BTC/USD','1Day',10)
    assert [r.status for r in rs] == ['BLOCKED','PROVIDER_VERIFIED']
def test_registry_stops_after_verified_provider():
    rs=ProviderRegistry([Good(),Blocked()]).fetch_first_verified('BTC/USD','1Day',10)
    assert len(rs)==1 and rs[0].status=='PROVIDER_VERIFIED'
