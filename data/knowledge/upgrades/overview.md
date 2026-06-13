# Upgrades — Overview (call flow)

**Systems used:** AWS, Carehub, Hansen

1. [AWS] Auto Answer
2. [AWS] Whisper with Query Type
3. [AWS] Capture name
4. [AWS] Paste number
5. [AWS] Copy Number
6. [AWS] Clear sapces in number
7. [AWS] Click Next
8. [AWS] Select account holder
9. [AWS] Select reason for call from level 1
10. [AWS] From level 1 selection, level 2 selection is selected
11. [AWS] From level 2 selection, level 3 selection is selected
12. [AWS] Select method to send Otac
13. [AWS] Select next
14. [AWS] Wait for customer to repeat Otac
15. [AWS] Enter Otac from customer and click next
16. [AWS] Inform customer DPA has failed and end call
17. **Decision — [AWS] DPA passed?**
   - If **YES**: Open Account
   - If **NO**: Inform customer DPA has failed and end call
18. [AWS] ACW (10 sec)
   - (end of this flow)
19. [AWS] Open Account
20. [Carehub] Click on account subscriptions
21. [Hansen] Click on details
22. [Carehub] Select Upgrade tab
23. [Carehub] Notify customer of reason
24. [Hansen] Confirm customer specifications
25. **Decision — [Carehub] Eligible?**
   - If **NO**: Notify customer of reason
   - If **YES**: Click on details
26. [Carehub] Select the correct number
27. [Carehub] Check Eligibility for upgrade
28. [Carehub] Leave Detailed Notes/ DPA result
29. [Carehub] Select Level 4 Disposition
30. [Carehub] Close Account
31. [AWS] Contact Telesales Consult Transfer
32. [AWS] Confirm customer details & query & internal pin
33. [AWS] Alternate to the customer
34. [AWS] Complete transfer

## Notes
- Steps to Triage calls (Find the correct process to use)
- OTAC is the OTP used as a security pin
