# -*- coding: utf-8 -*-
from odoo import models, api


class HrPayslip(models.Model):
    """ Extends the 'hr.payslip' model to include
    additional functionality related to employee loans."""
    _inherit = 'hr.payslip'

    def get_inputs(self, contract_ids, date_from, date_to):
        """Compute additional inputs for the employee payslip,
        considering active loans."""
        res = super(HrPayslip, self).get_inputs(contract_ids, date_from, date_to)
        
        # Get employee_id from contract or payslip
        employee_id = self.env['hr.contract'].browse(
            contract_ids[0].id).employee_id if contract_ids else self.employee_id
        
        # Find all approved loans for the employee
        loan_ids = self.env['hr.loan'].search(
            [('employee_id', '=', employee_id.id), ('state', '=', 'approve')])
        
        # Initialize total loan amount for the period
        total_loan_amount = 0.0
        
        # Loop through all approved loans
        for loan in loan_ids:
            # Loop through all loan lines (installments) for the loan
            for loan_line in loan.loan_lines:
                # Ensure the loan line date is within the payslip period
                # and the loan line is not paid
                if (date_from <= loan_line.date <= date_to and not loan_line.paid and not loan_line.is_manual_payment):
                    # Accumulate the loan amount
                    total_loan_amount += loan_line.amount

        # Update the payslip input with the total loan amount
        for result in res:
            if result.get('code') == 'LO':  # 'LO' is the code for loan input
                result['amount'] = total_loan_amount

        return res

    def action_payslip_done(self):
        """Mark loan lines as paid and recompute the total loan amount
        when the payslip is confirmed."""
        for line in self.input_line_ids:
            if line.loan_line_id and not line.loan_line_id.is_manual_payment:
                # Mark the loan line as paid
                line.loan_line_id.paid = True
                # Recompute the total loan amount
                line.loan_line_id.loan_id._compute_total_amount()
        return super(HrPayslip, self).action_payslip_done()

    @api.model
    def write(self, vals):
        """Override the write method to invalidate the cache
        and force recomputation of fields in the payroll module."""
        res = super(HrPayslip, self).write(vals)
        
        # Invalidate the cache for the updated records
        if self.ids:
            self.env.invalidate_all()
        
        return res
