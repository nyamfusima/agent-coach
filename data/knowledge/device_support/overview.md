# Device Support — Overview (call flow)

**Systems used:** Carehub, Device Help, Smart Agent

1. [Smart Agent] Auto Answer
2. [Device Help] Identify make & Model of device
3. [Smart Agent] Whisper with Query Type
4. [Smart Agent] Capture name
5. [Smart Agent] Paste number
6. [Smart Agent] Copy Number
7. [Smart Agent] Clear spaces in Number
8. [Smart Agent] Click Next
9. [Smart Agent] Select account holder
10. [Smart Agent] Select reason for call from level 1
11. [Smart Agent] From level 1 selection, level 2 selection is selected
12. [Smart Agent] From level 2 selection, level 3 selection is selected
13. [Smart Agent] Select method to send Otac
14. [Smart Agent] Select next
15. [Smart Agent] Wait for customer to repeat Otac
16. [Smart Agent] Enter Otac from customer and click next
17. [Smart Agent] Inform customer DPA has failed and end call
18. **Decision — [Smart Agent] DPA passed?**
   - If **YES**: Open Account
   - If **NO**: Inform customer DPA has failed and end call
19. [Smart Agent] ACW (10 sec)
   - (end of this flow)
20. [Smart Agent] Open Account
21. [Carehub] Select Device Help from drop down
22. [Carehub] Leave Detailed Notes/ DPA result
23. [Carehub] Select Level 4 Disposition
24. [Carehub] Close Account

## Notes
- Steps to Triage calls (Find the correct process to use)
- OTAC is the OTP used as a security pin
