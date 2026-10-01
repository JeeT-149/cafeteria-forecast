$ErrorActionPreference = "Stop"

Write-Host "1. Verifying data/Cafeteria Order Data.sql exists..."
if (-Not (Test-Path "data/Cafeteria Order Data.sql")) {
    Write-Error "The original 11 GB SQL dump is not stored in this repository. For full reproduction, obtain the assignment-provided 'Cafeteria Order Data.sql' file and place it at: data/Cafeteria Order Data.sql"
    exit 1
}

Write-Host "2. Starting MySQL Docker container..."
# Try to stop and remove if it exists to avoid duplicate-container errors, then start
docker compose down -v
docker compose up -d db

Write-Host "3. Waiting until MySQL is ready..."
$maxRetries = 20
$retryCount = 0
$ready = $false
while (-not $ready -and $retryCount -lt $maxRetries) {
    $status = docker inspect -f '{{.State.Health.Status}}' (docker compose ps -q db)
    if ($status -eq "healthy") {
        $ready = $true
        Write-Host "MySQL is ready!"
    } else {
        Start-Sleep -Seconds 5
        $retryCount++
    }
}
if (-not $ready) {
    Write-Error "MySQL did not become ready in time."
    exit 1
}

Write-Host "4. Extracting the required 7 tables..."
docker compose run --rm app python src/extract_tables.py

Write-Host "5. Fixing SQL terminators..."
docker compose run --rm app python src/fix_sql_terminators.py

Write-Host "6. Loading tables into MySQL..."
$tables = @("branches", "counters", "dishes", "categories", "order_has_statuses", "orders", "order_details")
foreach ($t in $tables) {
    Write-Host "   Loading $t..."
    docker compose exec db sh -c "mysql -uroot -ppass cafe < /tables/$t.sql"
}

Write-Host "7. Creating required indexes..."
docker compose exec db mysql -uroot -ppass cafe -e "CREATE INDEX idx_order_date ON orders(order_date);"
docker compose exec db mysql -uroot -ppass cafe -e "CREATE INDEX idx_branch_order_date ON orders(branch_id, order_date);"
docker compose exec db mysql -uroot -ppass cafe -e "CREATE INDEX idx_counter_id ON orders(counter_id);"
docker compose exec db mysql -uroot -ppass cafe -e "CREATE INDEX idx_order_id ON order_details(order_id);"

Write-Host "8. Running src/clean.py..."
docker compose run --rm app python src/clean.py

Write-Host "9. Running src/top_items.py..."
docker compose run --rm app python src/top_items.py

Write-Host "10. Running src/eda.py..."
docker compose run --rm app python src/eda.py

Write-Host "11. Running src/forecast_extra.py..."
docker compose run --rm app python src/forecast_extra.py 2 1

Write-Host "12. Running src/audit_docs.py..."
docker compose run --rm app python src/audit_docs.py

Write-Host "13. Running pytest..."
docker compose run --rm app pytest -q

Write-Host "14. Final success message"
Write-Host "Reproduction complete! Results are in data/processed/ and reports/."
