# Essentials — Overview (call flow)

**Systems used:** AWS, Carehub

1. [AWS] Auto Answer
2. [AWS] Whisper with Query Type
3. [AWS] Capture name
4. [AWS] Paste number
5. [AWS] Copy Number
6. [AWS] Clear spaces in number
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
20. [Carehub] Leave Detailed Notes/ DPA result
21. [Carehub] Select Level 4 Disposition
22. [Carehub] Close Account

## Notes
- Steps to Triage calls (Find the correct process to use)
- OTAC is the OTP used as a security pin
