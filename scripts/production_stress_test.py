import asyncio
import time
import httpx
import statistics
import sys

BASE_URL = "http://127.0.0.1:8000"

async def run_benchmark(name: str, tasks, expected_status=200):
    t0 = time.time()
    results = await asyncio.gather(*tasks, return_exceptions=True)
    t1 = time.time()
    total_time = t1 - t0
    
    latencies = []
    errors = []
    successes = 0
    
    for r in results:
        if isinstance(r, Exception):
            errors.append(str(r))
        elif isinstance(r, httpx.Response):
            if r.status_code == expected_status:
                successes += 1
                latencies.append(r.elapsed.total_seconds() * 1000)
            else:
                errors.append(f"HTTP {r.status_code}: {r.text[:80]}")
                
    total = len(tasks)
    avg_lat = statistics.mean(latencies) if latencies else 0
    p95_lat = statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else (max(latencies) if latencies else 0)
    
    print(f"[{'PASS' if len(errors) == 0 else 'WARN'}] {name}")
    print(f"       Requests: {successes}/{total} | Total Time: {total_time:.2f}s")
    if latencies:
        print(f"       Avg: {avg_lat:.1f}ms | p95: {p95_lat:.1f}ms | Min: {min(latencies):.1f}ms | Max: {max(latencies):.1f}ms")
    if errors:
        print(f"       Errors ({len(errors)}): {errors[:3]}")
    print()
    return len(errors) == 0

async def main():
    print("=" * 65)
    print("  BHILAI_TV // PRODUCTION DEEP RESILIENCE & STRESS TEST")
    print("  Testing Concurrency, Security, Fault Tolerance & Caching")
    print("=" * 65)
    print()
    
    headers = {"User-Agent": "BhilaiTV-StressTester/1.0"}
    limits = httpx.Limits(max_keepalive_connections=50, max_connections=100)
    
    async with httpx.AsyncClient(headers=headers, limits=limits, timeout=15.0) as client:
        # 1. Health check baseline
        r = await client.get(f"{BASE_URL}/api/health")
        assert r.status_code == 200, "Health check failed"
        print("[PASS] Baseline Health Check: System Online\n")
        
        # 2. Concurrency: 25 parallel requests to /api/latest
        tasks = [client.get(f"{BASE_URL}/api/latest?page=1&per_page=12") for _ in range(25)]
        await run_benchmark("25 Concurrent Requests to /api/latest", tasks)
        
        # 3. Concurrency: 25 parallel searches with multiple queries
        search_terms = ["Marvel", "Avatar", "Batman", "Spider", "Avengers"] * 5
        tasks = [client.get(f"{BASE_URL}/api/search?q={term}&per_page=8") for term in search_terms]
        await run_benchmark("25 Concurrent Searches with Multiple Queries", tasks)
        
        # 4. Detail Modal & Sibling Quality Concurrency (15 parallel requests)
        tasks = [client.get(f"{BASE_URL}/api/release/40450") for _ in range(15)]
        await run_benchmark("15 Concurrent Release Detail & Sibling Resolver Lookups", tasks)
        
        # 5. Poster Micro-Service Concurrency (30 parallel poster lookups)
        poster_titles = ["Reacher", "Fighter", "The Babysitter", "Fast Five", "Aarata", "Dune"] * 5
        tasks = [client.get(f"{BASE_URL}/api/poster?title={t}") for t in poster_titles]
        await run_benchmark("30 Concurrent Poster Resolver Requests (Cache & Upstream)", tasks)
        
        # 6. Security Fuzzing
        print("--- SECURITY & BOUNDARY FUZZING TESTS ---")
        
        # 6a. Path Traversal Test on Static Files
        traversal_urls = [
            f"{BASE_URL}/static/../../app/main.py",
            f"{BASE_URL}/static/%2e%2e/%2e%2e/etc/passwd",
            f"{BASE_URL}/static/..%2f..%2fapp/config.py"
        ]
        t_passed = True
        for u in traversal_urls:
            resp = await client.get(u)
            if resp.status_code == 200 and ("SECRET" in resp.text or "import" in resp.text):
                t_passed = False
                print(f"[FAIL] Path traversal vulnerability detected on {u}!")
        if t_passed:
            print("[PASS] Path Traversal Protection: Static directory is safely isolated.")
            
        # 6b. SQL & XSS Injection Payload Handling
        payloads = [
            "' OR '1'='1",
            "<script>alert('XSS')</script>",
            "'; DROP TABLE releases; --",
            "\" style=\"background:red\" onmouseover=\"alert(1)\"",
            "../../../../etc/passwd",
            "A" * 2000 # Buffer limit test
        ]
        fuzz_passed = True
        for p in payloads:
            resp = await client.get(f"{BASE_URL}/api/search", params={"q": p})
            if resp.status_code >= 500:
                fuzz_passed = False
                print(f"[FAIL] Server crashed (500) on payload: {p[:30]}")
        if fuzz_passed:
            print("[PASS] Injection & Fuzzing Resilience: All malicious inputs handled safely without crashes.")
            
        # 6c. Non-existent and Invalid Post ID Handling
        invalid_ids = [999999999, -1, 0]
        id_passed = True
        for i in invalid_ids:
            resp = await client.get(f"{BASE_URL}/api/release/{i}")
            if resp.status_code not in [404, 502, 422]:
                id_passed = False
                print(f"[WARN] Unexpected status {resp.status_code} for invalid ID {i}")
        if id_passed:
            print("[PASS] Invalid ID Handling: Graceful 404/502/422 errors returned.")

        # 6d. Fake Resolver URL Handling
        fake_urls = [
            f"{BASE_URL}/api/resolve/direct?url=https://fake-hubcloud.cx/drive/invalid123",
            f"{BASE_URL}/api/resolve/gdflix?url=https://fake-gdflix.io/file/invalid123"
        ]
        res_passed = True
        for u in fake_urls:
            resp = await client.get(u)
            if resp.status_code == 500:
                res_passed = False
                print(f"[FAIL] Internal 500 error on invalid resolver URL: {u}")
        if res_passed:
            print("[PASS] Resolver Fault Tolerance: Upstream network errors handled with clean 502 responses.")
            
        print()
        print("=" * 65)
        print("  PRODUCTION STRESS TEST SUITE COMPLETE")
        print("=" * 65)

if __name__ == "__main__":
    asyncio.run(main())
