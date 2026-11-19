/* -*- c++ -*- */
/*
 * Copyright 2021 Anton Ottosson.
 *
 * This is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 3, or (at your option)
 * any later version.
 *
 * This software is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this software; see the file COPYING.  If not, write to
 * the Free Software Foundation, Inc., 51 Franklin Street,
 * Boston, MA 02110-1301, USA.
 */

#ifndef INCLUDED_IEEE802_11_EXTRACT_CSI_IMPL_H
#define INCLUDED_IEEE802_11_EXTRACT_CSI_IMPL_H

#include <ieee802_11/extract_csi.h>
#include <fstream>
#include <cstdint>
#include <set>
#include <string>

namespace gr {
namespace ieee802_11 {

class extract_csi_impl : public extract_csi
{
private:
    pmt::pmt_t d_meta;
    std::vector<gr_complex> d_csi;

    std::ofstream d_csv;
    std::string d_csv_path;
    uint64_t d_packet_counter;

    // Filters: lowercase MAC strings, or "any" to disable that filter.
    std::string d_target_ta;
    std::string d_target_ra;

    // Every distinct "ta|ra" pair is printed once, so a rotated MAC
    // is visible on the console immediately.
    std::set<std::string> d_seen_pairs;

    uint64_t d_last_report_us;
    int d_current_channel;

public:
    extract_csi_impl();
    ~extract_csi_impl();

    void handle_pdu(pmt::pmt_t pdu);

    int work(int noutput_items,
             gr_vector_const_void_star& input_items,
             gr_vector_void_star& output_items);
             
    void set_channel(int chan) override;
};

} // namespace ieee802_11
} // namespace gr

#endif /* INCLUDED_IEEE802_11_EXTRACT_CSI_IMPL_H */
