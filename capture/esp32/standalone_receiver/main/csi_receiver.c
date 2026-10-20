#include <stdio.h>
#include <string.h>
#include <math.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_wifi.h"
#include "esp_log.h"
#include "nvs_flash.h"

static const char *TAG = "CSI_RX";

// This is the custom MAC address my Transmitter is broadcasting
const uint8_t EXPECTED_MAC[6] = {0x1A, 0x2B, 0x3C, 0x4D, 0x5E, 0x6F};

void csi_callback(void *ctx, wifi_csi_info_t *info) {

    int8_t *csi_data = (int8_t *)info->buf;
    
    // 2. Print prefix for our CSV file
    printf("CSI_DATA"); 
    
    // 3. Loop through the 64 subcarriers and calculate amplitude
    for (int i = 0; i < 64; i++) {
        int8_t imaginary = csi_data[i * 2];
        int8_t real = csi_data[(i * 2) + 1];
        
        // Amplitude = sqrt(real^2 + imag^2)
        float amplitude = sqrt(pow(real, 2) + pow(imaginary, 2));
        printf(",%.1f", amplitude);
    }
    printf("\n");
}

void app_main() {
    // Initialize storage and Wi-Fi drivers
    nvs_flash_init();
    esp_netif_init();
    esp_event_loop_create_default();
    
    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    cfg.csi_enable = 1; 
    esp_wifi_init(&cfg);
    
    esp_wifi_set_mode(WIFI_MODE_STA);
    esp_wifi_start();
    
    // Enable Promiscuous mode and lock onto Channel 6 to match the Transmitter
    esp_wifi_set_promiscuous(true);
    esp_wifi_set_channel(6, WIFI_SECOND_CHAN_NONE);
    
    // Configure CSI hardware extraction
    wifi_csi_config_t csi_config = {
        .lltf_en = true,
        .htltf_en = true,
        .stbc_htltf2_en = true,
        .ltf_merge_en = true,
        .channel_filter_en = true,
        .manu_scale = false,
        .shift = false
    };
    esp_wifi_set_csi_config(&csi_config);
    
    // Start listening!
    esp_wifi_set_csi_rx_cb(csi_callback, NULL);
    
    ESP_LOGI(TAG, "Receiver optimized for Channel 6. Awaiting frames...");
}