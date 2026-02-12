echo "========================================"
echo "  Запуск тестов Memeow"
echo "========================================"
echo

# Цвета для вывода
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Функция для запуска тестов с таймером
run_tests() {
    local app=$1
    echo -e "${YELLOW}Тестирование $app...${NC}"
    
    # Замеряем время выполнения
    start_time=$(date +%s.%N)
    
    # Запускаем тесты
    python manage.py test $app --verbosity=1
    
    exit_code=$?
    
    end_time=$(date +%s.%N)
    duration=$(echo "$end_time - $start_time" | bc)
    
    if [ $exit_code -eq 0 ]; then
        echo -e "${GREEN}✓ Тесты $app пройдены за ${duration}с${NC}"
    else
        echo -e "${RED}✗ Тесты $app не пройдены${NC}"
    fi
    
    echo
    return $exit_code
}

# Проверяем наличие bc для вычислений
if ! command -v bc &> /dev/null; then
    echo "Установите bc для более точного замера времени: sudo apt-get install bc"
    duration_fn() { echo "N/A"; }
fi

echo "Создание тестовой базы данных..."
echo

# Запускаем тесты для приложений
run_tests memes.tests.test_models
run_tests memes.tests.test_forms
run_tests memes.tests.test_views
run_tests memes.tests.test_api
run_tests memes.tests.test_middleware
run_tests memes.tests.test_utils
run_tests memes.tests.test_mailing

run_tests users.tests.test_models
run_tests users.tests.test_forms
run_tests users.tests.test_views
run_tests users.tests.test_signals

echo "========================================"
echo -e "${GREEN}Все тесты завершены!${NC}"
echo "========================================"

# Показываем покрытие кода, если установлен coverage
if command -v coverage &> /dev/null; then
    echo
    echo "Запуск coverage..."
    coverage run --source='memes,users' manage.py test
    coverage report -m
fi