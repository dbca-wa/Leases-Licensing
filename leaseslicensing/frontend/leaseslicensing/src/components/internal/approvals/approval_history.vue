<template lang="html">
    <div id="approvalHistory">
        <modal
            transition="modal fade"
            :title="'History for Approval ' + approvalLodgementNumber"
            :extra-large="true"
            cancel-text="Close"
            ok-text=""
            @cancel="close()"
        >
            <div class="container-fluid">
                <div class="row">
                    <alert v-if="errorString" type="danger"
                        ><strong>{{ errorString }}</strong></alert
                    >
                    <div class="col-sm-12">
                        <div class="form-group">
                            <div class="row">
                                <div v-if="approvalId" class="col-lg-12">
                                    <datatable
                                        :id="datatable_id"
                                        ref="history_datatable"
                                        :dt-options="datatable_options"
                                        :dt-headers="datatable_headers"
                                    />
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </modal>
    </div>
</template>
<script>
import modal from '@vue-utils/bootstrap-modal.vue';
import alert from '@vue-utils/alert.vue';
import { helpers, api_endpoints, constants, utils } from '@/utils/hooks.js';
import datatable from '@/utils/vue/datatable.vue';
import { v4 as uuid } from 'uuid';

export default {
    name: 'ApprovalHistory',
    components: {
        modal,
        alert,
        datatable,
    },
    props: {
        approvalId: {
            type: Number,
            required: true,
        },
        approvalLodgementNumber: {
            type: String,
            required: true,
        },
    },
    data: function () {
        return {
            datatable_id: 'history-datatable-' + uuid(),
            approvalDetails: {
                approvalLodgementNumber: null,
            },
            isModalOpen: false,
            messageDetails: '',
            ccEmail: '',
            validation_form: null,
            errorString: '',
            successString: '',
            success: false,
        };
    },
    computed: {
        csrf_token: function () {
            return helpers.getCookie('csrftoken');
        },
        datatable_headers: function () {
            return [
                'id',
                'Number',
                'Type',
                'Holder',
                'Proposal',
                'Status',
                // 'Version Comment',
                'Issue Date',
                // 'Reason',
                'Expiry Date',
                'Document',
                'Letter',
                // 'Action',
            ];
        },
        column_id: function () {
            return {
                // 1. ID
                data: 'id',
                orderable: false,
                searchable: false,
                visible: false,
                render: function (row, type, full) {
                    return full.id;
                },
            };
        },
        column_lodgement_number: function () {
            return {
                // 2. Lodgement Number
                data: 'id',
                orderable: true,
                searchable: true,
                visible: true,
                render: function (row, type, full) {
                    return full.lodgement_number;
                },
            };
        },
        column_type: function () {
            return {
                data: 'id',
                orderable: true,
                searchable: true,
                visible: true,
                render: function (row, type, full) {
                    return full.approval_type.name;
                },
            };
        },
        column_holder: function () {
            return {
                data: 'id',
                orderable: true,
                searchable: true,
                visible: true,
                render: function (row, type, full) {
                    return full.holder;
                },
            };
        },
        column_application: function () {
            return {
                data: 'id',
                orderable: true,
                searchable: true,
                visible: true,
                render: function (row, type, full) {
                    return `<a href="${full.application_detail_url}" target="_blank">${full.application}</a>`;
                },
            };
        },
        column_approval_status: function () {
            return {
                data: 'id',
                orderable: true,
                searchable: true,
                visible: true,
                render: function (row, type, full) {
                    return full.status;
                },
            };
        },
        column_version_date: function () {
            return {
                data: 'id',
                orderable: true,
                searchable: true,
                visible: true,
                render: function (row, type, full) {
                    return full.version_date_str;
                },
            };
        },
        column_expiry_date: function () {
            return {
                data: 'id',
                orderable: true,
                searchable: true,
                visible: true,
                render: function (row, type, full) {
                    return full.expiry_date_str;
                },
            };
        },
        column_reason: function () {
            return {
                data: 'id',
                orderable: true,
                searchable: true,
                visible: true,
                render: function (row, type, full) {
                    return full.reason;
                },
            };
        },
        column_revision_comment: function () {
            return {
                data: 'id',
                orderable: true,
                searchable: true,
                visible: true,
                render: function (row, type, full) {
                    return full.revision_comment;
                },
            };
        },
        column_license_document: function () {
            return {
                data: 'id',
                orderable: true,
                searchable: true,
                visible: true,
                render: function (row, type, full) {
                    if (!full.licence_document) return '';
                    let filename = full.licence_document.filename
                        ? full.licence_document.filename
                        : 'Approval.PDF';
                    return `<div><a href='${full.licence_document.url}' target='_blank'><i style='color:red;' class='fa fa-file-pdf'></i>${filename}</a></div>`;
                },
            };
        },
        column_cover_letter: function () {
            return {
                data: 'id',
                orderable: true,
                searchable: true,
                visible: true,
                render: function (row, type, full) {
                    if (!full.cover_letter) return '';
                    let filename = full.cover_letter.filename
                        ? full.cover_letter.filename
                        : 'CoverLetter.PDF';
                    return `<div><a href='${full.cover_letter.url}' target='_blank'><i style='color:red;' class='fa fa-file-pdf'></i>${filename}</a></div>`;
                },
            };
        },
        datatable_options: function () {
            let vm = this;
            let columns = [
                vm.column_id,
                vm.column_lodgement_number,
                vm.column_type,
                vm.column_holder,
                vm.column_application,
                vm.column_approval_status,
                // vm.column_revision_comment,
                vm.column_version_date,
                // vm.column_reason,
                vm.column_expiry_date,
                vm.column_license_document,
                vm.column_cover_letter,
            ];

            return {
                autoWidth: false,
                language: {
                    processing: constants.DATATABLE_PROCESSING_HTML,
                },
                responsive: true,
                searching: true,
                ordering: true,
                order: [[0, 'desc']],
                ajax: {
                    url: api_endpoints.lookupApprovalHistory(this.approvalId),
                    dataSrc: 'data',

                    // adding extra GET params for Custom filtering
                    // eslint-disable-next-line no-unused-vars
                    data: function (d) {},
                },
                dom: 'lBfrtip',
                buttons: [],
                columns: columns,
                processing: true,
            };
        },
    },
    created: function () {
        this.fetchApprovalDetails();
    },
    methods: {
        close: function () {
            this.errorString = '';
            this.isModalOpen = false;
            $('.has-error').removeClass('has-error');
        },
        fetchApprovalDetails: async function () {
            let vm = this;
            let url = api_endpoints.lookupApprovalHistory(this.approvalId);
            utils
                .fetchUrl(url)
                .then((data) => {
                    vm.approvalDetails = Object.assign({}, data);
                })
                .catch((error) => {
                    this.errorMessage = constants.ERRORS.API_ERROR;
                    console.error(`Error fetching approval details: ${error}`);
                });
        },
    },
};
</script>
