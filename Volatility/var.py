#List of variable for the volatility case 
nb_var = 11
list_var=[40]
list_var[0]="RTM"
i = 1
for i in range(1,nb_var):
    
    c1="RTM1C"+str(i+44)
    p1= "RTM1P"+str(i+44)
    c2= "RTM2C"+str(i+44)
    p2="RTM2P"+str(i+44)
    list_var.extend([c1,p1,c2,p2])
# list of variable for the first month 
j=1
for j in range(0,nb_var-1):
    del list_var[1+j*2]
    del list_var[1+j*2]
# list of varibale for the second month

