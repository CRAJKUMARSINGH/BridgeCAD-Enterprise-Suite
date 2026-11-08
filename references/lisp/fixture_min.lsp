(defun c:gad-deck () (setq dtop (+ rl -0.065) halfw 5.25)
  (command "LINE" (list 0.0 dtop) (list 12.0 dtop) "")
  (command "HATCH" "AR-SAND" 0.5 0))
