import React from 'react'
import { Button, ConfigProvider, Input, Modal } from 'antd'
import type { ModalProps } from 'antd'

import './pin-input-modal.style.css'
interface Props extends ModalProps {
  onSubmit: (code?: string) => void
}

const pinLength = 6

const PinInputModal = ({ open, onSubmit, onCancel }: Props) => {
  const [code, setCode] = React.useState('')

  return (
    <Modal
      title='Nhập mã PIN'
      open={open}
      footer={[
        <Button
          key='pinButton'
          className='border-2 !border-[#000] text-base font-normal !m-0 border-systemShockBlue !bg-white hover:!bg-[#202FA3] hover:!text-white !text-[#000] w-[100px] shadow-none rounded-3xl'
          size='large'
          onClick={() => {
            onSubmit(code)
            setCode('')
          }}
          disabled={code.length != pinLength}
        >
          Xác nhận
        </Button>
      ]}
      onCancel={onCancel}
      className='app-modal pin-input-modal'
      width={300}
    >
      <ConfigProvider
        theme={{
          components: {
            Input: {
              borderRadiusSM: 8,
              activeBorderColor: '#000',
              colorBorder: '#000',
              paddingBlockSM: 8,
              fontSize: 14
            }
          }
        }}
      >
        <Input.Password
          maxLength={pinLength}
          className='!border-[2px]'
          value={code}
          size='small'
          onChange={(e) => setCode(e.target.value)}
        />
      </ConfigProvider>
    </Modal>
  )
}
export default PinInputModal
