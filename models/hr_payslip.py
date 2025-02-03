# -*- coding: utf-8 -*-
#############################################################################
#    A part of Open HRMS Project <https://www.openhrms.com>
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import models, api


class HrPayslip(models.Model):
    """ Extends the 'hr.payslip' model to include
    additional functionality related to employee loans."""
    _inherit = 'hr.payslip'

    def get_inputs(self, contract_ids, date_from, date_to):
        """Compute additional inputs for the employee payslip,
        considering active loans.
        :param contract_ids: Contract ID of the current employee.
        :param date_from: Start date of the payslip.
        :param date_to: End date of the payslip.
        :return: List of dictionaries representing additional inputs for
        the payslip."""
        res = super(HrPayslip, self).get_inputs(contract_ids, date_from, date_to)
        
        # Ambil employee_id dari kontrak atau dari payslip
        employee_id = self.env['hr.contract'].browse(
            contract_ids[0].id).employee_id if contract_ids else self.employee_id
        
        # Cari semua loan yang disetujui (state = 'approve') untuk employee tersebut
        loan_ids = self.env['hr.loan'].search(
            [('employee_id', '=', employee_id.id), ('state', '=', 'approve')])
        
        # Inisialisasi total jumlah pinjaman yang harus dibayar dalam periode ini
        total_loan_amount = 0.0
        
        # Loop melalui semua loan yang disetujui
        for loan in loan_ids:
            # Loop melalui semua loan lines (angsuran) dari loan tersebut
            for loan_line in loan.loan_lines:
                # Pastikan loan_line.payment_date berada dalam rentang tanggal payslip
                # dan loan_line belum dibayar (paid = False)
                if (date_from <= loan_line.date <= date_to and not loan_line.paid and not loan_line.is_manual_payment):
                    # Akumulasi jumlah pinjaman yang harus dibayar
                    total_loan_amount += loan_line.amount

        # Update input payslip dengan total jumlah pinjaman
        for result in res:
            if result.get('code') == 'LO':  # 'LO' adalah kode untuk input loan
                result['amount'] = total_loan_amount
                # Jika diperlukan, Anda bisa menyimpan ID loan_line yang diproses
                #result['loan_line_id'] = loan_line.id

        return res

    def action_payslip_done(self):
        """ Compute the loan amount and remaining amount while confirming
            the payslip"""
        for line in self.input_line_ids:
            if line.loan_line_id and not line.loan_line_id.is_manual_payment:
                # Tandai loan_line sebagai sudah dibayar
                line.loan_line_id.paid = True
                # Hitung ulang total amount loan
                line.loan_line_id.loan_id._compute_total_amount()
        return super(HrPayslip, self).action_payslip_done()
    
    @api.model
    def write(self, vals):
        """Override the write method to trigger recomputation of fields
        in the payroll module when changes are made in the ohrms_loan module."""
        res = super(HrPayslip, self).write(vals)
    
        # Recompute specific fields if they are computed fields
        self.env['hr.payslip'].search([('id', 'in', self.ids)]).recompute()
    
        return res
