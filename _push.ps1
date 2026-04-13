Set-Location 'C:\TOPOLOGICA_BIOSECURITY\homology_cliff_repo'
gh repo create 'smaniches/homology-cliff' --private --source='.' --description='Homology cliff in frozen ESM-2 biosecurity retrieval v1.0: 5 papers, 4 pre-registrations, 9360 per-cell results with SHA256 manifest.' 2>&1
git remote -v
git branch -M main
git push -u origin main 2>&1 | Select-Object -Last 20
git push --tags 2>&1 | Select-Object -Last 5
