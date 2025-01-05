from odoo import models, fields, api, http
from odoo.http import request
from odoo.tools import consteq


class ResCompany(models.Model):
    _inherit = 'res.company'

    sign_folder_id = fields.Many2one(
        'documents.folder',
        string="Sign Folder",
        help="Folder where signed documents will be stored."
    )


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    sign_folder_id = fields.Many2one(
        related='company_id.sign_folder_id',
        readonly=False,
        string="Sign Folder",
    )


class SignRequest(models.Model):
    _inherit = 'sign.request'

    def _transfer_signed_file(self):
        for record in self:
            if record.state == 'signed':
                # Retrieve the folder from company settings
                folder_id = self.env.user.company_id.sign_folder_id.id
                if folder_id:
                    attachments = self.env['ir.attachment'].search([
                        ('res_model', '=', 'sign.request'),
                        ('res_id', '=', record.id)
                    ])
                    for attachment in attachments:
                        document_vals = {
                            'attachment_id': attachment.id,
                            'type': 'binary',
                            'folder_id': folder_id,
                        }
                        self.env['documents.document'].create(document_vals)


class Sign(http.Controller):
    @http.route(['/sign/sign_request_state/<int:request_id>/<token>'], type='json', auth='public')
    def get_sign_request_state(self, request_id, token):
        """
        Returns the state of a sign request.
        :param request_id: id of the request
        :param token: access token of the request
        :return: state of the request
        """
        sign_request = request.env['sign.request'].sudo().browse(request_id).exists()
        if not sign_request or not consteq(sign_request.access_token, token):
            return http.request.not_found()
        sign_request._transfer_signed_file()
        return sign_request.state
