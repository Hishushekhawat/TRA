import secrets
import uuid
from django.shortcuts import render,redirect
import pandas as pd
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from rest_framework.parsers import JSONParser
from .models import *
from .forms import *
from django.contrib.auth.hashers import check_password,make_password
import random
from django.conf import settings
from django.core.mail import send_mail
from .udf import *
from django.db.models import F,Q
from django.core.paginator import Paginator
from .serializers import *
from dateutil.parser import parse
import datetime
import csv
from django.db.models.functions import Concat


# Create your views here.

def home(request):
    try:
        if authenticate(request):
            if request.method == "GET":
                sources = Sources.objects.all().count()
                leads = Leads.objects.all().count()
                redundant = Redundant_data.objects.all().count()
                context = {"sources": sources, "leads":leads, "redundant":redundant}
                return render(request, 'dashboard.html', context)
        return redirect('login')   
    except Exception as e:
        return render(request, "exception.html", {"message": f"Unknown Error - {e}"})

def source_detail(request):
    try:
        if authenticate(request):
            if request.method == "GET":
                source_list = []
                sources = Sources.objects.all()
                for source in sources:
                    data = {}
                    data['name'] = source.name
                    data['leads'] = Leads.objects.filter(source_id=source.id).count()
                    data['redundant'] = Redundant_data.objects.filter(source_id=source.id).count()
                    source_list.append(data)
                if source_list != []:
                    p = Paginator(source_list, 9)
                    page_number = request.GET.get('page')
                    try:
                        page_obj = p.get_page(page_number)
                    except PageNotAnInteger:
                        page_obj = p.page(1)
                    except EmptyPage:
                        page_obj = p.page(p.num_pages)
                    context = {'page_obj': page_obj}
                    return render(request, 'source_detail.html', context)
                    return render(request, 'source_detail.html', {"source": source_list})
        return redirect('login')   
    except Exception as e:
        return render(request, "exception.html", {"message": f"Unknown Error - {e}"})

def login(request):
    try:
        if request.method == 'GET':
            try:
                user_token = request.session["user_token"]
            except:
                user_token = ""
            if user_token  == "":
                return render(request, 'login.html')
            return redirect("user")
        if request.method == 'POST':
            email = request.POST.get("email")
            password = request.POST.get("password")
            user_data = user_profile.objects.filter(email=email) 
            print(user_data)
            if user_data:
                request.session["username"] = f"{user_data[0].first_name} {user_data[0].last_name}"
                user_password = user_data[0].password
                if check_password(password, user_password):
                    if user_data[0].status == 'staff':
                        print("1")
                        session_token = f"{secrets.token_hex()}{uuid.uuid4}"
                        request.session["user_token"]= session_token
                        request.session["user_id"]= user_data[0].id
                        request.session["is_admin"]= False
                        return redirect("home")
                    
                    if user_data[0].status == 'admin':
                        print("2")
                        session_token = f"{secrets.token_hex()}{uuid.uuid4}"
                        request.session["user_token"]=session_token
                        request.session["user_id"]= user_data[0].id
                        request.session["is_admin"]= True
                        users = user_profile.objects.all()
                        # context = {"all_users_data" : users}
                        return redirect("home")
            return render(request,"login.html", {"message": "Enter a correct password"})
        return render(
                request, "login.html", {
                    "message": "No account found"}
            )       
    except Exception as e:
        return render(request, "exception.html", {"message": f"Unknown Error - {e}"})
    
# Add admin user
@csrf_exempt
def add_admin(request):
    try:
        if request.method == "POST":
            data = JSONParser().parse(request)
            first_name= data['first_name']
            last_name= data['last_name']
            email= data['email']
            phone= data['phone']
            password= data['password']
            user_profile.objects.create(first_name=first_name, last_name=last_name, email=email, phone=phone, password=make_password(password), status="admin")
            return JsonResponse({"status":"Success", "Message":"Admin Registered"})
        return JsonResponse({"status":"Failed", "Message":"Invalid request method"})            
    except Exception as e:
        return JsonResponse({"status":"failed","message": f"Unknown Error - {e}"})



def logout(request):
    try:
        if authenticate(request):
            if request.method == "GET":
                for key in list(request.session.keys()):
                    del request.session[key]
                return redirect('login')
            return redirect('home')   
    except Exception as e:
        return render(request, "exception.html", {"message": f"Unknown Error - {e}"})


def forget_password(request):
    try:
        if request.method == 'GET':
            return render(request, 'forget_password.html')
        if request.method == "POST":
            email = request.POST.get("email")
            try:
                check_mail = user_profile.objects.get(email=email)
                gen_otp = random.randint(100000,999999)
                check = User_Otp.objects.filter(user_id=check_mail.id)
                if check:
                    check.update(otp=gen_otp)
                else:
                    User_Otp.objects.create(otp=gen_otp, user=check_mail)
                subject = "TRA FORGET PASSWORD"
                message = f" Your password reset code for TRA account from mail {email} is {gen_otp}."
                email_from = settings.EMAIL_HOST_USER
                recipient = [email]
                send_mail(subject,message,email_from,recipient)
                return render(request, "reset-password.html", {"user_id":check_mail.id})
            except:           
                return render(request, 'forget_password.html',{"message":"Email not registered"})    
    except Exception as e:
        return render(request, "exception.html", {"message": f"Unknown Error - {e}"})



def reset_password(request):
    try:
        if request.method == "GET":
            return redirect('forget_password')
        if request.method == "POST":
            password = request.POST.get("password")
            confirm_password = request.POST.get("confirm_password")
            otp = request.POST.get("otp")
            id = request.POST.get("user_id")
            check_otp = User_Otp.objects.filter(user_id=id)
            # print(check_otp.created_at)
            if check_otp:
                if int(check_otp[0].otp) == int(otp):
                    if password == confirm_password:
                        user_profile.objects.filter(id=id).update(password=make_password(password))
                        return redirect('login')
                    return render(request, "reset-password.html", {"message": "Password did't match", "user_id":id})
                return render(request, "reset-password.html", {"message": "Enter a correct code", "user_id":id})
            return render(request, 'forget_password.html', {"message": "Please enter email to get code."})
    except Exception as e:
        return render(request, "exception.html", {"message": f"Unknown Error - {e}"})          



def sources(request):
    try:
        if authenticate(request):
            if request.method == "GET":
                data = Sources.objects.all().order_by('id')
                if data:
                    p = Paginator(data, 10)
                    page_number = request.GET.get('page')
                    try:
                        page_obj = p.get_page(page_number)
                    except PageNotAnInteger:
                        page_obj = p.page(1)
                    except EmptyPage:
                        page_obj = p.page(p.num_pages)
                    context = {'page_obj': page_obj}
                    return render(request, 'sources.html', context)  
                return render(request, 'sources.html',{"no_data": "No sources"})         
            if request.method == "POST":
                source_name = request.POST.get("name")
                print(source_name)
                source_data = Sources_Form(request.POST or None)
                if source_data.is_valid():
                    source_data.save()
                    data = Sources.objects.all()
                    return redirect("sources") 
        return redirect('login')
    except Exception as e:
        return render(request, "exception.html", {"message": f"Unknown Error - {e}"})


def search_source(request):
    try:
        if authenticate(request):
            if request.method == "POST":
                query = request.POST.get("query")
                data = Sources.objects.filter(name__icontains=query)
                if data:
                    request.session['search_source'] = query
                    p = Paginator(data, 1)
                    page_number = request.GET.get('page')
                    try:
                        page_obj = p.get_page(page_number)
                    except PageNotAnInteger:
                        page_obj = p.page(1)
                    except EmptyPage:
                        page_obj = p.page(p.num_pages)
                    context = {'page_obj': page_obj}
                    return render(request, 'sources.html', context)  
                return render(request, 'sources.html',{"no_data": "No sources"})
            if request.method == "GET":
                query = request.session['search_source']
                data = Sources.objects.filter(name__icontains=query)
                if data:
                    p = Paginator(data, 1)
                    page_number = request.GET.get('page')
                    try:
                        page_obj = p.get_page(page_number)
                    except PageNotAnInteger:
                        page_obj = p.page(1)
                    except EmptyPage:
                        page_obj = p.page(p.num_pages)
                    context = {'page_obj': page_obj}
                    return render(request, 'sources.html', context)  
                return redirect('sources')
        return redirect('login') 
    except Exception as e:
        return render(request, "exception.html", {"message": f"Unknown Error - {e}"})
                


def del_source(request, pk):
    try:
        if authenticate(request):
            if request.method == "GET":
                Sources.objects.filter(id=pk).delete()
                return redirect('sources') 
        return redirect('login')    
    except Exception as e:
        return render(request, "exception.html", {"message": f"Unknown Error - {e}"})  
    


def update_source(request):
    try:
        if authenticate(request):
            if request.method == "POST":
                name = request.POST.get("name")
                id = request.POST.get("id")
                Sources.objects.filter(id=id).update(name=name)
                return redirect('sources')
        return redirect('login')    
    except Exception as e:
        return render(request, "exception.html", {"message": f"Unknown Error - {e}"})  
            


def leads(request):
    try:
        if authenticate(request):
            if request.method == "GET":
                try:
                    del request.session["lead_filter_by"]
                    del request.session["lead_filter_data"]
                except:
                    pass
                source_data = Sources.objects.all()
                data = Leads.objects.all().order_by('id')
                if data:
                    p = Paginator(data, 20)
                    page_number = request.GET.get('page')
                    try:
                        page_obj = p.get_page(page_number)
                    except PageNotAnInteger:
                        page_obj = p.page(1)
                    except EmptyPage:
                        page_obj = p.page(p.num_pages)
                    context = {'page_obj': page_obj, 'source':source_data}
                    return render(request, 'leads.html',context)
                else:
                    return render(request, 'leads.html',{"no_data":"No Leads Available"})
        return redirect('login')
    except Exception as e:
        return render(request, "exception.html", {"message": f"Unknown Error - {e}"})



@csrf_exempt
def lead_details(request, id):
    try:
        if authenticate(request):
            if request.method == "GET":
                data = Leads.objects.filter(id=id)
                if data:
                    json_data = LeadSerializer(data[0])
                    new_data = json_data.data
                    new_data['source'] = Sources.objects.get(id=int(json_data.data['source'])).name
                    return JsonResponse({"status": "Success", "data": new_data})
                return JsonResponse({"status": "Failed", "message": "No Data Found"})
            return JsonResponse({"status":"failed", "message":"invalid request method"})
        return redirect('login')   
    except Exception as e:
        return render(request, "exception.html", {"message": f"Unknown Error - {e}"})       




def del_lead(request,pk):
    try:
        if authenticate(request):
            if request.method == "GET":
                Leads.objects.filter(id=pk).delete()
                return redirect('leads')
        return redirect('login')    
    except Exception as e:
        return render(request, "exception.html", {"message": f"Unknown Error - {e}"})




def search_lead(request):
    try:
        if authenticate(request):
            if request.method == "POST":
                filter_by = ''
                filter_data = ''
                email = request.POST.get("email")
                source = request.POST.get("source")
                if source != None and email != None and email != "":
                    filter_by = "both"
                    filter_data = "both"
                    data = Leads.objects.filter(source_id=source, email__icontains=email).order_by('id')
                                
                elif email != None and email != "":
                    if "@" in email:
                        filter_by = "email"
                        filter_data = email
                        data = Leads.objects.filter(email__icontains=email).order_by('id')
                    else:
                        filter_by = "name"
                        filter_data = email
                        x = email.split()
                        data = Leads.objects.filter(Q(first_name__contains=x[0]) | Q(last_name__contains=x[1])).order_by('id')
                
                elif source != None:
                    filter_by = "source"
                    filter_data = source
                    data = Leads.objects.filter(source_id=source).order_by('id')
                # p_date = request.POST.get("purchase_date")
                # if p_date != "" and p_date != None:
                #     filter_by = "p_date"
                #     filter_data = p_date
                #     data = Leads.objects.filter(purchase_date=str(p_date)).order_by('id')     
                # i_date = request.POST.get("import_date")
                # if i_date != None and i_date != "":
                #     filter_by = "i_date"
                #     filter_data = i_date
                #     data = Leads.objects.filter(import_date=i_date).order_by('id') 
                if data:
                    request.session["lead_filter_by"] = filter_by
                    request.session["lead_filter_data"] = filter_data        
                    p = Paginator(data, 20)
                    page_number =  request.GET.get('page')
                    try:
                        page_obj = p.get_page(page_number)
                    except PageNotAnInteger:
                        page_obj = p.page(1)
                    except EmptyPage:
                        page_obj = p.page(p.num_pages)
                    source_data = Sources.objects.all()
                    context = {'page_obj': page_obj, 'source':source_data}
                    return render(request, 'leads.html',context)
                return render(request, 'leads.html', {"no_data": "No matching query found"})
            if request.method == "GET":
                try:
                    type = request.session["lead_filter_by"]
                    data = request.session["lead_filter_data"]
                except:
                    return redirect('leads')
                if type == "email":
                    data =  Leads.objects.filter(email__icontains=data).order_by('id')
                if type == "source":
                    data = Leads.objects.filter(source_id=data).order_by('id')
                # if type == "p_date":
                #     data = Leads.objects.filter(purchase_date=str(data)).order_by('id')
                # if type == "i_date":
                #     data = Leads.objects.filter(import_date=data).order_by('id') 
                p = Paginator(data, 20)
                page_number = request.GET.get('page')
                try:
                    page_obj = p.get_page(page_number)
                except PageNotAnInteger:
                    page_obj = p.page(1)
                except EmptyPage:
                    page_obj = p.page(p.num_pages)
                source_data = Sources.objects.all()
                context = {'page_obj': page_obj, 'source':source_data}
                return render(request, 'leads.html',context)
        return redirect('login')
    except Exception as e:
        return render(request, "exception.html", {"message": f"Unknown Error - {e}"}) 

def export_lead(request):
    # try:
        if authenticate(request):
            if request.method == "GET":
                try:
                    type = request.session["lead_filter_by"]
                    data = request.session["lead_filter_data"]
                    if type == "email":
                        data =  Leads.objects.filter(email__icontains=data).order_by('id')
                    if type == "source":
                        data = Leads.objects.filter(source_id=data).order_by('id')
                    response = HttpResponse(content_type="text/csv")
                    response[
                        "Content-Disposition"
                    ] = "attachment; filename={name}{ext}".format(
                        name="Export", ext=".csv"
                    )
                    writer = csv.writer(response)
                    writer.writerow(["FirstName" ,"LastName", "Email" , "Phone", "Source", "City", "State", "Address", "Debt-Amount", "Cost", "Opt-In-Ip", "Import_date", "Purchase_date"])
                    for row in data:
                        writer.writerow([row.first_name , row.last_name, row.email, row.phone, row.source, row.city, row.state, row.address, row.debt_amount, row.cost, row.opt_in_ip, row.import_date, row.purchase_date])
                    return response
                except:
                    data = Leads.objects.all().order_by('id')
                    response = HttpResponse(content_type="text/csv")
                    response[
                        "Content-Disposition"
                    ] = "attachment; filename={name}{ext}".format(
                        name="Export", ext=".csv"
                    )
                    writer = csv.writer(response)
                    writer.writerow(["FirstName" ,"LastName", "Email" , "Phone", "Source", "City", "State", "Address", "Debt-Amount", "Cost", "Opt-In-Ip", "Import_date", "Purchase_date"])
                    for row in data:
                        writer.writerow([row.first_name , row.last_name, row.email, row.phone, row.source, row.city, row.state, row.address, row.debt_amount, row.cost, row.opt_in_ip, row.import_date, row.purchase_date])
                    return response
        return redirect('login')
    # except Exception as e:
    #     return render(request, "exception.html", {"message": f"Unknown Error - {e}"})               


def imports(request):
    try:
        if authenticate(request):
            if request.method == "GET":
                data = Sources.objects.all()
                return render(request, 'import.html',{"source_data":data})            
            if request.method =="POST":
                file = request.FILES.get('file')
                source_id = request.POST.get('source')
                print(file, source_id, file.name)
                if str(file).endswith(".csv"):
                    s_data = Sources.objects.all()
                    df = pd.read_csv(file)
                    columns = df.columns.values
                    print(columns)
                    save_lead = Leads_File.objects.create(file=file, file_name=file.name, source_id=source_id)
                    return render(request, 'import.html', {"columns": columns, "source_data": s_data, "file_id": save_lead.id, "source_id":source_id })
                return JsonResponse({"status":"failed", "message":"invalid file format"})
        return redirect('login')
    except Exception as e:
        return render(request, "exception.html", {"message": f"Unknown Error - {e}"})




@csrf_exempt
def save_leads_column(request): 
    try:
        if authenticate(request):
            if request.method =="POST":
                file_id = request.POST.get('file_id')
                source_id = request.POST.get('source_id')
                first_name_sel_col = request.POST.get('first_name')
                last_name_sel_col = request.POST.get('last_name')
                city_sel_col = request.POST.get('city')
                state_sel_col = request.POST.get('state')
                address_sel_col = request.POST.get('address')
                debt_amount_sel_col = request.POST.get('debt_amount')
                phone_sel_col = request.POST.get('phone')
                email_sel_col = request.POST.get('email')
                opt_in_ip_sel_col = request.POST.get('opt_in_ip')
                cost_sel_col = request.POST.get('cost')
                purchase_date_sel_col = request.POST.get('purchase_date')
                import_date_sel_col = request.POST.get('import_date')
                file_data = Leads_File.objects.filter(id=file_id)
                file = file_data[0].file
                if file_data[0].file_name.endswith(".csv"):
                    df = pd.read_csv(file)
                    col = list(df.columns.values)
                    col_value = {}           
                    for i in col:
                        col_value[i] = list(df[i])
                    for i in range(len(df)):
                        check_email =  col_value.get(email_sel_col)[i]
                        check = Leads.objects.filter(email=check_email)
                        if check:
                            re_check = Redundant_data.objects.filter(email=check_email)
                            if re_check:
                                before = int(re_check[0].redund_count) + 1
                                re_check.update(redund_count = before)
                            else:
                                Redundant_data.objects.create(email=check_email, redund_count=1, file_id=file_id, source_id=source_id)
                        else:
                            Leads.objects.create(first_name = col_value.get(first_name_sel_col)[i] , last_name = col_value.get(last_name_sel_col)[i],
                                city = col_value.get(city_sel_col)[i] , state = col_value.get(state_sel_col)[i], address = col_value.get(address_sel_col)[i],
                                debt_amount = col_value.get(debt_amount_sel_col)[i], phone = col_value.get(phone_sel_col)[i], email = col_value.get(email_sel_col)[i],
                                opt_in_ip = col_value.get(opt_in_ip_sel_col)[i], cost = col_value.get(cost_sel_col)[i], purchase_date = parse(col_value.get(purchase_date_sel_col)[i]),
                                source_id = source_id)
                    final_data = Redundant_data.objects.filter(file_id=file_id)
                    if final_data:
                        print("1")
                        return render(request, "redundant.html", {"redund_data":final_data})
                    else:
                        print("2")
                        return redirect("leads")
                return JsonResponse({"status":"failed", "message":"invalid file format"})                
        return redirect('login')
    except Exception as e:
        return render(request, "exception.html", {"message": f"Unknown Error - {e}"})

def user(request):
    try:
        if authenticate(request):
            if request.method == "GET":
                data = user_profile.objects.all().order_by('id')
                if data:
                    p = Paginator(data, 10)
                    page_number = request.GET.get('page')
                    try:
                        page_obj = p.get_page(page_number)
                    except PageNotAnInteger:
                        page_obj = p.page(1)
                    except EmptyPage:
                        page_obj = p.page(p.num_pages)
                    context = {'page_obj': page_obj}
                    return render(request, 'users.html', context)
                return render(request, 'users.html', {"no_data": "No Staff Users"})
        return redirect('login')
    except Exception as e:
        return render(request, "exception.html", {"message": f"Unknown Error - {e}"})



def search_user(request):
    try:
        if authenticate(request):
            if request.method == "POST":
                query = request.POST.get('query')
                type = request.POST.get('select_type')
                status = request.POST.get('status')
                if query == "" and type == None and status == None or query == "" and type != None and status == None:
                    return redirect('user')
                if query == "" and type == None and status != None:
                    request.session['search_with'] = 1
                    request.session['search_status'] = status
                    data = user_profile.objects.filter(status=status)
                elif status == None:
                    request.session['search_with'] = 2
                    request.session['search_query'] = query
                    request.session['search_type'] = type
                    if type == "first_name":
                        data = user_profile.objects.filter(first_name__icontains=query)
                    elif type == "last_name":
                        data = user_profile.objects.filter(last_name__icontains=query)
                    elif type == "email":
                        data = user_profile.objects.filter(email__icontains=query)
                    elif type == "phone":
                        data = user_profile.objects.filter(phone__icontains=query)
                elif status != None:
                    request.session['search_with'] = 3
                    request.session['search_query'] = query
                    request.session['search_status'] = status
                    request.session['search_type'] = type
                    if type == "first_name":
                        data = user_profile.objects.filter(first_name__icontains=query, status=status)
                    elif type == "last_name":
                        data = user_profile.objects.filter(last_name__icontains=query, status=status)
                    elif type == "email":
                        data = user_profile.objects.filter(email__icontains=query, status=status)
                    elif type == "phone":
                        data = user_profile.objects.filter(phone__icontains=query, status=status)
                if data:
                    p = Paginator(data, 1)
                    page_number = request.GET.get('page')
                    try:
                        page_obj = p.get_page(page_number)
                    except PageNotAnInteger:
                        page_obj = p.page(1)
                    except EmptyPage:
                        page_obj = p.page(p.num_pages)
                    context = {'page_obj': page_obj}
                    return render(request, 'users.html', context)
                return render(request, 'users.html',{"no_data": "No matching query found"})
            if request.method == "GET":
                if request.session['search_with'] == 1:
                    status = request.session['search_status']
                    data = user_profile.objects.filter(status=status)
                elif request.session['search_with'] == 2:
                    query =request.session['search_query']
                    type = request.session['search_type']
                    if type == "first_name":
                        data = user_profile.objects.filter(first_name__icontains=query)
                    elif type == "last_name":
                        data = user_profile.objects.filter(last_name__icontains=query)
                    elif type == "email":
                        data = user_profile.objects.filter(email__icontains=query)
                    elif type == "phone":
                        data = user_profile.objects.filter(phone__icontains=query)
                elif request.session['search_with'] == 3:
                    query = request.session['search_query']
                    status = request.session['search_status']
                    type = request.session['search_type']
                    if type == "first_name":
                        data = user_profile.objects.filter(first_name__icontains=query, status=status)
                    elif type == "last_name":
                        data = user_profile.objects.filter(last_name__icontains=query, status=status)
                    elif type == "email":
                        data = user_profile.objects.filter(email__icontains=query, status=status)
                    elif type == "phone":
                        data = user_profile.objects.filter(phone__icontains=query, status=status)
                if data:
                    p = Paginator(data, 1)
                    page_number = request.GET.get('page')
                    try:
                        page_obj = p.get_page(page_number)
                    except PageNotAnInteger:
                        page_obj = p.page(1)
                    except EmptyPage:
                        page_obj = p.page(p.num_pages)
                    context = {'page_obj': page_obj}
                    return render(request, 'users.html', context)
                return render(request, 'users.html',{"no_data": "No matching query found"})
        return redirect('login') 
    except Exception as e:
        return render(request, "exception.html", {"message": f"Unknown Error - {e}"})
        
   


def del_user(request,pk):
    try:
        if authenticate(request):
            if request.method == "GET":
                user_profile.objects.filter(id=pk).delete()
                return redirect('user')
        return redirect('login')
    except Exception as e:
        return render(request, "exception.html", {"message": f"Unknown Error - {e}"})



def update_user(request):
    try:
        if authenticate(request):
            if request.method =="POST":
                id = request.POST.get('id')
                password = request.POST.get('password')
                status = request.POST.get('status')
                confirm_password = request.POST.get('confirm_password')
                user_data_instance = user_profile.objects.get(id=id)
                old_pass = user_data_instance.password
                updated_data = User_Profile_Form(request.POST or None, instance=user_data_instance)
                if password == confirm_password:
                    if updated_data.is_valid():
                        if password != None and password != "null" and password != "":
                            partial_data = updated_data.save(commit=False)
                            partial_data.password= make_password(password)
                            if status != None:
                                partial_data.status = status
                            partial_data.save()
                            return redirect('user')
                        else:
                            if status != None:
                                partial_data = updated_data.save(commit=False)
                                partial_data.status = status
                                partial_data.save()
                            else:
                                partial_data = updated_data.save(commit=False)
                                partial_data.password = old_pass
                                partial_data.save()
                            return redirect('user')
                return render(request, 'users.html', {"message": "Password should be same"})
        return redirect('login')    
    except Exception as e:
        return render(request, "exception.html", {"message": f"Unknown Error - {e}"})  


def user_register(request):
    try:
        if authenticate(request):
            if request.method == "GET":
                return render(request,'user_add.html')
            if request.method == "POST":
                password = request.POST.get('password')
                confirm_password = request.POST.get('confirm_password')
                status = request.POST.get('status')
                user_data = User_Profile_Form(request.POST or None)
                if password == confirm_password:
                    if user_data.is_valid():
                        partial_data = user_data.save(commit=False)
                        if password != None and password != "null" and password != "":
                            partial_data.password= make_password(password)
                            partial_data.status = status
                            partial_data.save()
                            return redirect('user')
                    print(user_data.errors)
                    return render(request, 'user_add.html', {"message": user_data.errors})
                return render(request, 'user_add.html', {"message": "Password should be same"})
        return redirect('login')            
    except Exception as e:
        return render(request, "exception.html", {"message": f"Unknown Error - {e}"})



def page_not_found_view(request):
    return render(request, "404.html")


def page_server_error_view(request):
    return render(request, "500.html")

def file(request):
    try:
        if authenticate(request):
            if request.method == "GET":
                file_list = []
                data = []
                data_ = Redundant_data.objects.all()
                for d in data_:
                    if d.file_id not in file_list:
                        file_list.append(d.file_id)
                        data.append(d)
                if data != []:
                    print(data)
                    p = Paginator(data, 10)
                    page_number = request.GET.get('page')
                    try:
                        page_obj = p.get_page(page_number)
                    except PageNotAnInteger:
                        page_obj = p.page(1)
                    except EmptyPage:
                        page_obj = p.page(p.num_pages)
                    context = {'page_obj': page_obj}
                    return render(request, 'files.html', context)
                return render(request, "files.html", {"empty_data": "No Redundant Data"})
        return redirect('login') 
    except Exception as e:
        return render(request, "exception.html", {"message": f"Unknown Error - {e}"})

def file_detail(request, file_name):
    try:
        if authenticate(request):
            if request.method == "GET":
                data = Redundant_data.objects.filter(file__file_name=file_name)
                if data:
                    p = Paginator(data, 10)
                    page_number = request.GET.get('page')
                    try:
                        page_obj = p.get_page(page_number)
                    except PageNotAnInteger:
                        page_obj = p.page(1)
                    except EmptyPage:
                        page_obj = p.page(p.num_pages)
                    context = {'page_obj': page_obj, "file_name": file_name}
                    return render(request, 'file_detail.html', context)
                return render(request, "file_detail.html", {"empty_data": "No Redundant Data"})
        return redirect('login') 
    except Exception as e:
        return render(request, "exception.html", {"message": f"Unknown Error - {e}"})

def search_file(request):
    try:
        if authenticate(request):
            if request.method == "POST":
                file = request.POST.get("query")
                request.session['re_file'] = file
                data = Redundant_data.objects.filter(file__file_name = file)
                if data:
                    p = Paginator(data, 10)
                    page_number = request.GET.get('page')
                    try:
                        page_obj = p.get_page(page_number)
                    except PageNotAnInteger:
                        page_obj = p.page(1)
                    except EmptyPage:
                        page_obj = p.page(p.num_pages)
                    context = {'page_obj': page_obj}
                    return render(request, 'files.html', context)
                return render(request, "files.html", {"empty_data": "No Matching File Data"})
            if request.method == "GET":
                file = request.session['re_file'] 
                data = Redundant_data.objects.filter(file__file_name = file)
                if data:
                    p = Paginator(data, 10)
                    page_number = request.GET.get('page')
                    try:
                        page_obj = p.get_page(page_number)
                    except PageNotAnInteger:
                        page_obj = p.page(1)
                    except EmptyPage:
                        page_obj = p.page(p.num_pages)
                    context = {'page_obj': page_obj}
                    return render(request, 'files.html', context)
                return render(request, "files.html", {"empty_data": "No Matching File Data"})
            return render(request, "files.html", {"empty_data": "No Redundant Data"})
        return redirect('login') 
    except Exception as e:
            return render(request, "exception.html", {"message": f"Unknown Error - {e}"})





# @csrf_exempt
# def source_data(request):
#     try:
#         with transaction.atomic():
#             if request.method == "POST":
#                 form = Sources_Form(request.POST,request.FILES)
#                 if form.is_valid():
#                     form.save()
#                     print("my tra",form)
#                     return JsonResponse({"status":"success","message":"the source name is added successfully"})
#                 return JsonResponse({"status":"failed", "message":"form is not valid"})
            
                        
#             if request.method == "PUT":
#                 id = request.POST.get('id')
#                 name = request.POST.get('name')
#                 check=Sources.objects.filter(id=id)
#                 print("checking", check)
#                 return JsonResponse({"status":"success","message":"the source name is updated successfully"})
#             return JsonResponse({"status":"failed", "message":"request method in not valid"})
#     except Exception as e:
#         return JsonResponse({"status":"failed","message": f"Unknown Error - {e}"})




# @csrf_exempt
# def del_source_data(request):
#     try:
#         with transaction.atomic():
#             if request.method == "POST":
#                 id = request.POST.get('id')
#                 check=Sources.objects.filter(id=id).delete()
#                 print("helooo",check)
#                 return JsonResponse({"status":"success","message":"the source name is deleted successfully"})
#             return JsonResponse({"status":"failed", "message":"the request method is not valid"})    
#     except Exception as e:
#         return JsonResponse({"status":"failed","message": f"Unknown Error - {e}"})


# def del_user(request):
#     try:
#         if request.method == "GET":
#             return render(request, 'login.html')  
#             id = request.POST.get("id")
#             user_profile.objects.filter(id=id).delete()
#             return JsonResponse({"status":"success", "message":"user deleted successfully"})
#     except Exception as e:
#         return JsonResponse({"status":"failed","message": f"Unknown Error - {e}"})


# @csrf_exempt
# def pop_up_lead(request):
#     # try:
#         # if authenticate(request):
#         if request.method == "GET":            
#             data= JSONParser().parse(request)
#             id= data["id"]
#             pop_up = Leads.objects.filter(id=id)
#             print(pop_up)
#             return JsonResponse({"status":"success", "data":pop_up})
#         return JsonResponse({"status":"failed", "message":"invalid request method"}) 
#         # return render(
#         #         request, "login.html", {"message": "Unauthenticated user"})    
#     # except Exception as e:
#     #     return JsonResponse({"status":"failed","message": f"Unknown Error - {e}"})




# @csrf_exempt
# def display(request):
    # # try:
    #     if request.method == 'POST':
    #         file = request.FILES.get('file')
    #         file_name = request.POST.get('file_name')
    #         if file != None:


    #             # lead = Leads_File.objects.all()
    #             # print(lead.first_name)
    #             # return HttpResponse(lead)
    #             df = pd.read_csv(file)
    #             col = df.columns.values
    #             col1 = ', '.join(col)
                # col1=col[3]
                # print(type(col1))
                # a = df.columns[3]
                # b= df[a]
                # print(col1)
                # return JsonResponse({"status":"pass"})
    # except Exception as e:
    #    return JsonResponse({"status":"failed","message": f"Unknown Error - {e}"})
    

# def upload_lead(request):
#     try:
#         if request.method == "POST":
#             file_name = request.POST.get("file_name")
#             file = request.FILES.get("file")
#             if str(file).endswith(".csv") or str(file).endswith(".xlsx"):
#                 return render(request, '')
#     except Exception as e:
#        return JsonResponse({"status":"failed","message": f"Unknown Error - {e}"})

