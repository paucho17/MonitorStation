#pragma once
#include <Arduino.h>
#define ESP_SLEEP_WAKEUP_UNDEFINED 0
int esp_sleep_get_wakeup_cause();
void esp_sleep_enable_timer_wakeup(uint64_t);
void esp_deep_sleep_start();
