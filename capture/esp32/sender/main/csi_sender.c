#include <stdio.h>
#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_wifi.h"
#include "esp_log.h"
#include "nvs_flash.h"
#include "esp_netif.h"
#include "esp_event.h"

static const char *TAG = "CSI_TX";

// A minimal 802.11 Data frame payload
// We set a specific Source MAC so your Receiver knows exactly what to look for
uint8_t raw_frame[] = {
    0x08, 0x01, 0x00, 0x00,             // Frame Control (Data), Duration
    0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, // Destination MAC (Broadcast)
    0x1A, 0x2B, 0x3C, 0x4D, 0x5E, 0x6F, // Source MAC (Custom identifier)
    0x1A, 0x2B, 0x3C, 0x4D, 0x5E, 0x6F, // BSSID
    0x00, 0x00,                         // Sequence Control
    0x00, 0x00, 0x00, 0x00,             // QoS Control
    'C', 'S', 'I', '_', 'F', 'A', 'L', 'L' // Our custom payload
};

void tx_task(void *pvParameters) {
    while (1) {
        // Inject the raw frame directly into the air
        esp_err_t err = esp_wifi_80211_tx(WIFI_IF_STA, raw_frame, sizeof(raw_frame), true);
        if (err != ESP_OK) {
            ESP_LOGE(TAG, "TX Failed: %s", esp_err_to_name(err));
        }
        
        // 10ms delay = 100 packets per second (100 Hz). 
        // Adjust this based on how fast you want to sample movements.
        vTaskDelay(pdMS_TO_TICKS(10)); 
    }
}

void app_main() {
    // 1. Initialize Non-Volatile Storage (required by WiFi driver)
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        nvs_flash_erase();
        nvs_flash_init();
    }

    // 2. Initialize standard TCP/IP and WiFi
    esp_netif_init();
    esp_event_loop_create_default();
    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    esp_wifi_init(&cfg);

    // 3. Set to Station mode and start
    esp_wifi_set_mode(WIFI_MODE_STA);
    esp_wifi_start();

    // 4. Enable Promiscuous Mode (required for raw injection)
    esp_wifi_set_promiscuous(true);

    // 5. Set the Channel
    // IMPORTANT: The transmitter and receiver MUST be on the exact same channel.
    esp_wifi_set_channel(6, WIFI_SECOND_CHAN_NONE);

    // 6. Spawn the FreeRTOS transmission task
    ESP_LOGI(TAG, "Starting raw WiFi frame injection on Channel 6...");
    xTaskCreate(tx_task, "tx_task", 2048, NULL, 5, NULL);
}