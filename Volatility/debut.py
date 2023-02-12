#List of variable for the volatility case 
def var_list (month):
    nb_var = 11
    list_var=[40]
    list_var[0]="RTM"
    if month ==1 :
            for i in range(1,nb_var):
                
                c1="RTM1C"+str(i+44)
                p1= "RTM1P"+str(i+44)
                c2= "RTM2C"+str(i+44)
                p2="RTM2P"+str(i+44)
                list_var.extend([c1,p1,c2,p2])
                
    else:  
        for i in range(1,nb_var):
                
            c2= "RTM2C"+str(i+44)
            p2="RTM2P"+str(i+44)
            list_var.extend([c2,p2])
        
    return(list_var)
