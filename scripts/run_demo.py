import os
import sys
import subprocess

def main():
    print("=============================================")
    print("      UDYAM SETU - DEMO INITIALIZATION       ")
    print("=============================================")
    
    scripts_dir = os.path.dirname(__file__)
    setup_script = os.path.join(scripts_dir, "demo_setup.py")
    
    print("\n[1/3] Running Database Setup & Seeding...")
    # Run setup script and auto-confirm 'yes' to clear tables
    process = subprocess.Popen(
        [sys.executable, setup_script],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    
    output, _ = process.communicate(input="yes\n")
    print(output)
    
    if process.returncode != 0:
        print("❌ Demo setup failed.")
        sys.exit(1)
        
    print("\n[2/3] Infrastructure Verification")
    print("Checking if infrastructure is running...")
    
    import requests
    try:
        res = requests.get("http://localhost:8000/health", timeout=2)
        if res.status_code == 200:
            print("✓ Backend API detected.")
        else:
            print(f"❌ Backend API returned status {res.status_code}")
            sys.exit(1)
    except Exception as e:
        print("❌ Backend API is not reachable at http://localhost:8000 (is it running?)")
        sys.exit(1)
        
    try:
        docker_ps = subprocess.check_output(["docker", "ps"], text=True)
        if "postgres" in docker_ps.lower() or "timescaledb" in docker_ps.lower():
            print("✓ PostgreSQL Database detected.")
        else:
            print("❌ PostgreSQL container not found in docker ps")
            sys.exit(1)
            
        if "redis" in docker_ps.lower():
            print("✓ Redis detected.")
        else:
            print("❌ Redis container not found in docker ps")
            sys.exit(1)
    except Exception as e:
        print("❌ Failed to run docker ps. Is docker running?")
        sys.exit(1)
    
    print("\n[3/3] Ready for Presentation")
    print("To start the frontend dashboard, run in a new terminal:")
    print("  cd frontend && npm start")
    print("\nGood luck with the demo!")

if __name__ == "__main__":
    main()
