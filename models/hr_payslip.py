# -*- coding: utf-8 -*-
from odoo import models, api


class HrPayslip(models.Model):
    """ Extends the 'hr.payslip' model to include
    additional functionality related to employee loans."""
    _inherit = 'hr.payslip'

    def get_inputs(self, contract_ids, date_from, date_to):
        """Compute additional inputs for the employee payslip,
        considering active loans."""
        res = super().get_inputs(contract_ids, date_from, date_to)
        
        # Ambil employee_id dari kontrak atau payslip
        employee_id = contract_ids[0].employee_id if contract_ids else self.employee_id
        
        # Cari semua pinjaman yang disetujui untuk karyawan tersebut
        loan_ids = self.env['hr.loan'].search([
            ('employee_id', '=', employee_id.id),
            ('state', '=', 'approve')
        ])
        
        # Hitung total pinjaman yang harus dibayar dalam periode ini
        total_loan_amount = sum(
            loan_line.amount for loan in loan_ids for loan_line in loan.loan_lines
            if date_from <= loan_line.date <= date_to and not loan_line.paid and not loan_line.is_manual_payment
        )

        # Update input payslip dengan total jumlah pinjaman
        for result in res:
            if result.get('code') == 'LO':  # 'LO' adalah kode input loan
                result['amount'] = total_loan_amount

        return res

    def action_payslip_done(self):
        """Compute the loan amount and update the remaining amount upon confirmation."""
        for line in self.input_line_ids:
            if line.loan_line_id and not line.loan_line_id.is_manual_payment:
                line.loan_line_id.paid = True
                line.loan_line_id.loan_id._compute_total_amount()

        return super().action_payslip_done()

    def write(self, vals):
        """Override the write method to trigger recomputation of computed fields."""
        res = super().write(vals)

        # Refresh cache untuk memastikan perhitungan ulang computed fields
        self.invalidate_cache()

        return res
