# -*- coding: utf-8 -*-
from odoo import models, api, fields
import logging

_logger = logging.getLogger(__name__)


class HrPayslip(models.Model):
    """ Extends the 'hr.payslip' model to include
    additional functionality related to multiple loans."""
    _inherit = 'hr.payslip'

    loan_amount = fields.Float(string="Total Loan Amount", compute="_compute_loan_amount", store=True)

    def get_inputs(self, contract_ids, date_from, date_to):
        """Fetch loan deductions for the employee in the given payslip period."""
        res = super(HrPayslip, self).get_inputs(contract_ids, date_from, date_to)

        employee_id = self.env['hr.contract'].browse(
            contract_ids[0].id).employee_id if contract_ids else self.employee_id

        loan_lines = self.env['hr.loan.line'].search([
            ('loan_id.employee_id', '=', employee_id.id),
            ('date', '>=', date_from),
            ('date', '<=', date_to),
            ('paid', '=', False),
            ('is_manual_payment', '=', False)
        ])

        _logger.info("Found %s loan lines for employee %s", len(loan_lines), employee_id.name)

        # Hapus input lama yang memiliki kode 'LO' untuk mencegah duplikasi
        res = [r for r in res if r.get('code') != 'LO']

        # Tambahkan semua cicilan pinjaman ke payslip input
        for loan_line in loan_lines:
            res.append({
                'code': 'LO',
                'name': f"Loan Deduction ({loan_line.loan_id.name})",
                'amount': loan_line.amount,
                'loan_line_id': loan_line.id
            })

        return res

    def action_payslip_done(self):
        """When the payslip is confirmed, mark all related loan lines as paid."""
        _logger.info("Payslip %s is being confirmed", self.id)

        loan_lines_to_update = self.env['hr.loan.line']
        
        for line in self.input_line_ids:
            if line.loan_line_id and not line.loan_line_id.is_manual_payment:
                _logger.info("Marking loan line %s as paid", line.loan_line_id.id)
                loan_lines_to_update |= line.loan_line_id
        
        # Tandai semua loan_line_id sebagai 'paid = True'
        loan_lines_to_update.write({'paid': True})

        # Recompute total loan amount
        self._compute_loan_amount()

        return super(HrPayslip, self).action_payslip_done()

    @api.depends('input_line_ids')
    def _compute_loan_amount(self):
        """Compute the total loan amount for the payslip."""
        for payslip in self:
            payslip.loan_amount = sum(line.amount for line in payslip.input_line_ids if line.code == 'LO')

    @api.model
    def write(self, vals):
        """Ensure loan amount is recomputed when payslip input changes."""
        res = super(HrPayslip, self).write(vals)

        if 'input_line_ids' in vals:
            self._compute_loan_amount()

        return res


class HrPayslipInput(models.Model):
    """Extends hr.payslip.input to include a reference to the related loan line."""
    _inherit = 'hr.payslip.input'

    loan_line_id = fields.Many2one('hr.loan.line', string="Loan Line")
