
$jobName = "RobotmkAgent"
# Define the script block to be run in the background job
$jobScript = {
    # Convert the argument back to a hashtable
    $vars = $args[0]
    $number = 1
    foreach ($var in $vars.GetEnumerator()) {
        # Set each variable in the new scope
        #Set-Variable -Name $var.Name -Value $var.Value -Scope Global
        # try to set the variable. If it fails, it's probably a read-only variable
        # and we can ignore it.


        # $filename = "C:\foo\$number.dummy"
        # $var.GetType() | Out-File $filename
        # $number += 1
        # Continue

        try {
            Set-Variable -Name $var.Key -Value $var.Value -ErrorAction SilentlyContinue    
            #$varstring += "$($var.Key) = $($var.Value) - "
        }
        catch {
            $filename = "C:\foo\error.dummy"
            "foo" | Out-File -Append $filename
        }
        
    }
    
    # Write variables of inner scope
    $filename = "C:\foo\vars_inside.dummy"
    $vars | Out-File $filename
    $filename = "C:\foo\GetVariable_inside.dummy"
    Get-Variable | Out-File $filename

    $varFile = "C:\foo\varstring.dummy"
    #$varstring | Out-File $varFile
    # $vartable | Out-File "C:\foo\inside_vars.dummy"
}

# Create a hash table with all variables of the outer scope
$vars = @{}
Get-Variable | Where-Object { $_.Name -ne 'vars' } | ForEach-Object { $vars += @{ $_.Name = $_.Value } }

#$vars = Get-Variable | ForEach-Object { @{ $_.Name = $_.Value } }
# Write variables of outer scope
$filename = "C:\foo\vars_outside.dummy"
$vars | Out-File $filename
$filename = "C:\foo\GetVariable_outside.dummy"
Get-Variable | Out-File $filename

# $number = 1
# foreach ($var in $vars.GetEnumerator()) {
#     # Set each variable in the new scope
#     #Set-Variable -Name $var.Name -Value $var.Value -Scope Global
#     # try to set the variable. If it fails, it's probably a read-only variable
#     # and we can ignore it.
    
#     #Set-Variable -Name $var.Key -Value $var.Value -Scope Global -ErrorAction SilentlyContinue
#     # Append key and value to a string
#     #$varstring += $var.Key + ":" + $var.Value + " - "
#     # create file
#     $filename = "C:\foo\$number.dummy"
#     $var.GetType() | Out-File $filename
#     $number += 1
#     Continue
#     try {
#         Set-Variable -Name $var.Key -Value $var.Value -ErrorAction SilentlyContinue    
#         #$varstring += "$($var.Key) = $($var.Value) - "
#     }
#     catch {
#         $filename = "C:\foo\error.dummy"
#         "foo" | Out-File -Append $filename
#     }

# }


# Start the background job and pass the hashtable as an argument
$job = Start-Job -Name $jobName -ScriptBlock $jobScript -ArgumentList $vars
