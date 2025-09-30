from django.http import JsonResponse
from django.shortcuts import render
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib import messages
from django.urls import reverse
from django.utils.text import slugify

from coffee.upload import pathByDate, uploadFile, upload_editor_image
from .models import Document
from django.utils import timezone
import os
import urllib.parse
from django.core.files.storage import default_storage
from django.contrib.auth.decorators import login_required
import pandas as pd
import json
from coffee.helpers import extract_fields_from_pdf
# Document Views
class DocumentListView:
    @login_required(login_url="login_cms")
    def list_documents(request):
        per_page_options = [10, 25, 50, 100]

        per_page = request.GET.get('per_page', 10)

        query_name_search = request.GET.get('name_search')
        documents = Document.objects.all()
        
        if query_name_search:
            documents = documents.filter(
                Q(comco_ref__icontains=query_name_search) |
                Q(buyer_ref__icontains=query_name_search)
            )
            
        paginator = Paginator(documents, per_page)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        return render(request, 'documents/list.html', {'documents': page_obj, 'per_page_options': per_page_options, 'per_page': int(per_page),})
    
    @login_required(login_url="login_cms")
    def document_detail(request, code):
        document = get_object_or_404(Document, code=code)
        return render(request, 'documents/document_detail.html', {'document': document})
    
    @login_required(login_url="login_cms")
    def create_document(request):
        if request.method == 'POST':
            try:
                # Lấy dữ liệu từ request.POST
                print("request.POST::::", request.POST)
                comco_ref = request.POST.get('comco_ref')
                buyer_ref = request.POST.get('buyer_ref')
                contract_date = request.POST.get('contract_date')
                price = request.POST.get('price')
                dds_and_geo = request.POST.get('dds_and_geo')
                docs = request.POST.get('docs')
                shippers = request.POST.get('shippers')
                buyers = request.POST.get('buyers')
                shipment_period = request.POST.get('shipment_period')
                quality = request.POST.get('quality')
                quantity = request.POST.get('quantity')
                conts_no = request.POST.get('conts_no')
                packing = request.POST.get('packing')
                sample = request.POST.get('sample')
                result = request.POST.get('result')
                stuffing_date = request.POST.get('stuffing_date')
                carriers = request.POST.get('carriers')
                booking_no = request.POST.get('booking_no')
                etd = request.POST.get('etd')
                eta = request.POST.get('eta')
                destination = request.POST.get('destination')
                inspectors = request.POST.get('inspectors')
                warehouse = request.POST.get('warehouse')
                status = request.POST.get('status')
                weight_claim = request.POST.get('weight_claim')
                remark = request.POST.get('remark')
                
                document = Document(
                    comco_ref=comco_ref,
                    buyer_ref=buyer_ref,
                    contract_date=contract_date,
                    price=price,
                    dds_and_geo=dds_and_geo,
                    docs=docs,
                    shippers=shippers,
                    buyers=buyers,
                    shipment_period=shipment_period,
                    quality=quality,
                    quantity=quantity,
                    conts_no=conts_no,
                    packing=packing,
                    sample=sample,
                    result=result,
                    stuffing_date=stuffing_date,
                    carriers=carriers,
                    booking_no=booking_no,
                    etd=etd,
                    eta=eta,
                    destination=destination,
                    inspectors=inspectors,
                    warehouse=warehouse,
                    status=status,
                    weight_claim=weight_claim,
                    remark=remark,
                )
                document.save()
                
                return JsonResponse({
                    'status': 'success',
                    'message': 'Thêm hợp đồng thành công!',
                    'redirect': reverse('document-list')
                })
            except Exception as e:
                print("Error:", str(e))  # Debug log
                return JsonResponse({
                    'status': 'error',
                    'message': f'Lỗi khi thêm hợp đồng: {str(e)}'
                }, status=400)  
        
        return render(request, 'documents/create.html')
    
    @login_required(login_url="login_cms")
    def import_excel(request):
        if request.method == 'POST' and request.FILES.get('excel_file'):
            try:
                excel_file = request.FILES['excel_file']

                # Save the uploaded file temporarily
                temp_file_path = default_storage.save('temp/' + excel_file.name, excel_file)
                file_path = os.path.join(default_storage.location, temp_file_path)

                # Read Excel file
                df = pd.read_excel(file_path, header=0)  # Assuming first row is header

                # Expected columns based on Document model
                expected_columns = [
                    'comco_ref', 'buyer_ref', 'contract_date', 'price', 'dds_and_geo',
                    'docs', 'shippers', 'buyers', 'shipment_period', 'quality',
                    'quantity', 'conts_no', 'packing', 'sample', 'result',
                    'stuffing_date', 'carriers', 'booking_no', 'etd', 'eta',
                    'destination', 'inspectors', 'warehouse', 'status',
                    'weight_claim', 'remark'
                ]

                # Check if all required columns are present
                missing_columns = [col for col in expected_columns if col not in df.columns]
                if missing_columns:
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Các cột thiếu trong file Excel: {", ".join(missing_columns)}'
                    }, status=400)

                imported_count = 0
                error_count = 0
                errors = []

                for index, row in df.iterrows():
                    try:
                        # Convert date fields to proper format
                        contract_date = pd.to_datetime(row['contract_date']).date() if pd.notna(row['contract_date']) else None
                        stuffing_date = pd.to_datetime(row['stuffing_date']).date() if pd.notna(row['stuffing_date']) else None
                        etd = pd.to_datetime(row['etd']).date() if pd.notna(row['etd']) else None

                        document = Document(
                            comco_ref=str(row.get('comco_ref', '')),
                            buyer_ref=str(row.get('buyer_ref', '')),
                            contract_date=contract_date,
                            price=str(row.get('price', '')),
                            dds_and_geo=str(row.get('dds_and_geo', '')),
                            docs=str(row.get('docs', '')),
                            shippers=str(row.get('shippers', '')),
                            buyers=str(row.get('buyers', '')),
                            shipment_period=str(row.get('shipment_period', '')),
                            quality=str(row.get('quality', '')),
                            quantity=str(row.get('quantity', '')),
                            conts_no=str(row.get('conts_no', '')),
                            packing=str(row.get('packing', '')),
                            sample=str(row.get('sample', '')),
                            result=str(row.get('result', '')),
                            stuffing_date=stuffing_date,
                            carriers=str(row.get('carriers', '')),
                            booking_no=str(row.get('booking_no', '')),
                            etd=etd,
                            eta=str(row.get('eta', '')),
                            destination=str(row.get('destination', '')),
                            inspectors=str(row.get('inspectors', '')),
                            warehouse=str(row.get('warehouse', '')),
                            status=str(row.get('status', '')),
                            weight_claim=str(row.get('weight_claim', '')),
                            remark=str(row.get('remark', ''))
                        )
                        document.save()
                        imported_count += 1

                    except Exception as e:
                        error_count += 1
                        errors.append(f"Dòng {index + 2}")  # +2 because Excel rows start at 1 and header is row 1

                # Clean up temporary file
                if os.path.exists(file_path):
                    os.remove(file_path)    
                if error_count > 0:
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Import thất bại: {errors}'
                    }, status=400)
                
                message = f'Import thành công {imported_count} bản ghi.'

                return JsonResponse({
                    'status': 'success',
                    'message': message,
                    'imported_count': imported_count,
                })

            except Exception as e:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Lỗi khi import file Excel: {str(e)}'
                }, status=400)

        return JsonResponse({
            'status': 'error',
            'message': 'Phương thức không được hỗ trợ hoặc thiếu file Excel'
        }, status=405)

    @login_required(login_url="login_cms")
    def scan_pdf(request):
        if request.method == 'POST' and request.FILES.get('pdf_file'):
            try:
                pdf_file = request.FILES['pdf_file']
                extracted_data = extract_fields_from_pdf(pdf_file)
                
                print("extracted_data", extracted_data)
                return JsonResponse({
                    'status': 'success',
                    'message': 'Scan PDF thành công!',
                    'data': extracted_data
                })
                
            except Exception as e:
                print("e", e)
                return JsonResponse({
                    'status': 'error',
                    'message': f'Lỗi khi scan file PDF: {str(e)}'
                }, status=400)

        return JsonResponse({
            'status': 'error',
            'message': 'Phương thức không được hỗ trợ hoặc thiếu file PDF'
        }, status=405)

    @login_required(login_url="login_cms")
    def update_document(request, pk):
        document = get_object_or_404(Document, pk=pk)
        if request.method == 'POST':
            try:               
                comco_ref = request.POST.get('comco_ref')
                buyer_ref = request.POST.get('buyer_ref')
                contract_date = request.POST.get('contract_date')
                price = request.POST.get('price')
                dds_and_geo = request.POST.get('dds_and_geo')
                docs = request.POST.get('docs')
                shippers = request.POST.get('shippers')
                buyers = request.POST.get('buyers')
                shipment_period = request.POST.get('shipment_period')
                quality = request.POST.get('quality')
                quantity = request.POST.get('quantity')
                conts_no = request.POST.get('conts_no')
                packing = request.POST.get('packing')
                sample = request.POST.get('sample')
                result = request.POST.get('result')
                stuffing_date = request.POST.get('stuffing_date')
                carriers = request.POST.get('carriers')
                booking_no = request.POST.get('booking_no')
                etd = request.POST.get('etd')
                eta = request.POST.get('eta')
                destination = request.POST.get('destination')
                inspectors = request.POST.get('inspectors')
                warehouse = request.POST.get('warehouse')
                status = request.POST.get('status')
                weight_claim = request.POST.get('weight_claim')
                remark = request.POST.get('remark')

                document.comco_ref = comco_ref
                document.buyer_ref = buyer_ref
                document.contract_date = contract_date
                document.price = price
                document.dds_and_geo = dds_and_geo
                document.docs = docs
                document.shippers = shippers
                document.buyers = buyers
                document.shipment_period = shipment_period
                document.quality = quality
                document.quantity = quantity
                document.conts_no = conts_no
                document.packing = packing
                document.sample = sample
                document.result = result
                document.stuffing_date = stuffing_date
                document.carriers = carriers
                document.booking_no = booking_no
                document.etd = etd
                document.eta = eta
                document.destination = destination
                document.inspectors = inspectors
                document.warehouse = warehouse
                document.status = status
                document.weight_claim = weight_claim
                document.remark = remark

                document.save()
                return JsonResponse({
                    'status': 'success',
                    'message': 'Cập nhật hợp đồng thành công!',
                    'redirect': reverse('document-list')
                })
            except Exception as e:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Lỗi khi cập nhật hợp đồng: {str(e)}'
                }, status=400)
        
        return render(request, 'documents/update.html', {'document': document})

    @login_required(login_url="login_cms")
    def delete_document(request, pk):
        document = get_object_or_404(Document, pk=pk)
        if request.method == 'POST':
            try:    
                document.delete()
                return JsonResponse({
                    'status': 'success',
                    'message': 'Xóa hợp đồng thành công!',
                }, status=200)
            except Exception as e:
                return JsonResponse({
                    'status': 'error',
                    'message': f'Lỗi khi xóa hợp đồng: {str(e)}',
                }, status=400)