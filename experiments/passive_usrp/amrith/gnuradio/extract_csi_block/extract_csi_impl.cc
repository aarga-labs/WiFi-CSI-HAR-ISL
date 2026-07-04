/* -*- c++ -*- */
/*
 * WiFi Extract CSI block
 *
 * Copyright (C) 2026 Amrith B
 *
 * This block was added to the gr-ieee802.11 module
 * (https://github.com/bastibl/gr-ieee802-11), Copyright (C) Bastian
 * Bloessl and contributors, to extract per-subcarrier WiFi Channel
 * State Information (CSI) from decoded 802.11 frames for human
 * activity detection.
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program. If not, see <http://www.gnu.org/licenses/>.
 */

#ifdef HAVE_CONFIG_H
#include "config.h"
#endif

#include "extract_csi_impl.h"
#include <gnuradio/io_signature.h>
#include <algorithm>
#include <cctype>
#include <chrono>
#include <cstdlib>
#include <ctime>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <string>

// Configuration comes from environment variables so a MAC rotation or a
// new session never requires a recompile:
//   CSI_TA  - transmitter MAC to accept, or "any" (default below)
//   CSI_RA  - receiver MAC to accept, or "any" (default below)
//   CSI_OUT - output CSV path; unset -> timestamped file in DEFAULT_DIR
const std::string DEFAULT_TA = "YOUR_TRANSMITTER_MAC_ADDRESS";
const std::string DEFAULT_RA = "YOUR_RECEIVER_MAC_ADDRESS";
const std::string DEFAULT_DIR = "LOCATION_TO_SAVE_CSI_DATA_AS_CSV";

namespace {

std::string getenv_or(const char* name, const std::string& fallback)
{
    const char* v = std::getenv(name);
    return (v && *v) ? std::string(v) : fallback;
}

std::string to_lower(std::string s)
{
    std::transform(s.begin(), s.end(), s.begin(), [](unsigned char c) {
        return std::tolower(c);
    });
    return s;
}

std::string timestamped_csv_path()
{
    std::time_t t = std::time(nullptr);
    std::tm tm_buf;
    localtime_r(&t, &tm_buf);

    std::ostringstream oss;
    oss << DEFAULT_DIR << "/csi_" << std::put_time(&tm_buf, "%Y%m%d_%H%M%S")
        << ".csv";
    return oss.str();
}

uint64_t now_us()
{
    return std::chrono::duration_cast<std::chrono::microseconds>(
               std::chrono::system_clock::now().time_since_epoch())
        .count();
}

} // namespace

namespace gr {
namespace ieee802_11 {

extract_csi::sptr extract_csi::make()
{
    return gnuradio::get_initial_sptr(new extract_csi_impl());
}


extract_csi_impl::extract_csi_impl()
    : gr::sync_block("extract_csi",
                     gr::io_signature::make(0, 0, 0),
                     gr::io_signature::make(1, 1, 52 * sizeof(gr_complex)))
{
    message_port_register_in(pmt::mp("pdu in"));

    set_msg_handler(
    pmt::mp("pdu in"),
    boost::bind(
        &extract_csi_impl::handle_pdu,
        this,
        boost::placeholders::_1));

    d_packet_counter = 0;
    d_last_report_us = 0;

    d_target_ta = to_lower(getenv_or("CSI_TA", DEFAULT_TA));
    d_target_ra = to_lower(getenv_or("CSI_RA", DEFAULT_RA));
    d_csv_path = getenv_or("CSI_OUT", timestamped_csv_path());

    // Append so pointing CSI_OUT at an existing file never destroys it;
    // only write the header when the file is new/empty.
    bool need_header = true;
    {
        std::ifstream existing(d_csv_path);
        if (existing.good() && existing.peek() != std::ifstream::traits_type::eof())
            need_header = false;
    }

    d_csv.open(d_csv_path, std::ios::out | std::ios::app);

    if (!d_csv.is_open()) {
        std::cerr << "extract_csi: ERROR cannot open " << d_csv_path
                  << " for writing!" << std::endl;
    }

    if (need_header) {
        d_csv << "Packet,Timestamp_us";

        for (int i = 0; i < 52; i++) {
            d_csv << ",SC" << i << "_Re";
            d_csv << ",SC" << i << "_Im";
        }

        d_csv << "\n";
        d_csv.flush();
    }

    std::cout << "extract_csi: TA filter = " << d_target_ta
              << ", RA filter = " << d_target_ra << std::endl;
    std::cout << "extract_csi: writing to " << d_csv_path
              << (need_header ? "" : " (appending)") << std::endl;
}

extract_csi_impl::~extract_csi_impl()
{
    if (d_csv.is_open()) {
        d_csv.flush();
        d_csv.close();
    }

    std::cout << "extract_csi: total saved packets: " << d_packet_counter
              << " (" << d_csv_path << ")" << std::endl;
}

int extract_csi_impl::work(
    int noutput_items,
    gr_vector_const_void_star& input_items,
    gr_vector_void_star& output_items)
{
    return 0;
}
void extract_csi_impl::handle_pdu(pmt::pmt_t pdu)
{
    if (!pmt::is_pair(pdu))
        return;

    d_meta = pmt::car(pdu);

    //----------------------------------------------------
    // Must contain CSI
    //----------------------------------------------------
    if (!pmt::dict_has_key(d_meta, pmt::mp("csi")))
        return;

    //----------------------------------------------------
    // Must contain TA
    //----------------------------------------------------
    if (!pmt::dict_has_key(d_meta, pmt::mp("ta")))
        return;

    //----------------------------------------------------
    // Must contain RA
    //----------------------------------------------------
    if (!pmt::dict_has_key(d_meta, pmt::mp("ra")))
        return;

    std::string ta = to_lower(
        pmt::symbol_to_string(
            pmt::dict_ref(
                d_meta,
                pmt::mp("ta"),
                pmt::PMT_NIL)));

    std::string ra = to_lower(
        pmt::symbol_to_string(
            pmt::dict_ref(
                d_meta,
                pmt::mp("ra"),
                pmt::PMT_NIL)));

    //----------------------------------------------------
    // Filter packets
    //----------------------------------------------------
    bool match = (d_target_ta == "any" || ta == d_target_ta) &&
                 (d_target_ra == "any" || ra == d_target_ra);

    if (d_seen_pairs.insert(ta + "|" + ra).second) {
        std::cout << "extract_csi: seen TA=" << ta << " RA=" << ra
                  << (match ? " (MATCH)" : " (no match)") << std::endl;
    }

    if (!match)
        return;

    //----------------------------------------------------
    // Get CSI
    //----------------------------------------------------
    d_csi = pmt::c32vector_elements(
        pmt::dict_ref(
            d_meta,
            pmt::mp("csi"),
            pmt::PMT_NIL));

    //----------------------------------------------------
    // Save
    //----------------------------------------------------
    uint64_t t_us = now_us();

    d_csv << d_packet_counter++;
    d_csv << "," << t_us;

    for (auto c : d_csi)
    {
        d_csv << "," << c.real();
        d_csv << "," << c.imag();
    }

    d_csv << "\n";

    if (d_packet_counter % 100 == 0) {
        d_csv.flush();

        double rate = 0.0;
        if (d_last_report_us > 0 && t_us > d_last_report_us)
            rate = 100.0 * 1e6 / (double)(t_us - d_last_report_us);

        std::cout << "extract_csi: saved " << d_packet_counter << " packets";
        if (rate > 0.0)
            std::cout << " (~" << std::fixed << std::setprecision(1) << rate
                      << " rows/s)" << std::defaultfloat;
        std::cout << std::endl;

        d_last_report_us = t_us;
    }
}
} /* namespace ieee802_11 */
} /* namespace gr */
